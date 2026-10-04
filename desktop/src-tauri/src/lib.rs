//! Mutexx Advertiser - the desktop shell.
//!
//! The app itself is the Python program in this repository. This shell does four
//! things around it and nothing else:
//!
//! 1. starts the bundled Python on a free local port, with its data in
//!    `%LOCALAPPDATA%\Mutexx Production\Mutexx Advertiser` (the folder rule every
//!    Mutexx product follows), and makes sure it dies with the window;
//! 2. shows it in a native window instead of a browser tab;
//! 3. sends every link that leaves the app - a subreddit, a submit form, a forum -
//!    to the user's own browser, where they are signed in;
//! 4. checks for updates, signed with the Mutexx key, and asks before installing.

use std::fs::{self, File};
use std::io::{Read, Seek, SeekFrom};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::webview::PageLoadEvent;
use tauri::{Manager, RunEvent, Url, WebviewWindow, WebviewWindowBuilder};
use tauri_plugin_updater::{Update, UpdaterExt};

#[cfg(windows)]
use std::os::windows::process::CommandExt;

/// Without this a console window flashes up behind the app on every start.
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

/// How long the Python side gets to answer before the start screen says so.
const START_TIMEOUT: Duration = Duration::from_secs(45);

/// Tie child processes to the life of this process.
///
/// Closing the window cleanly is not enough: after a crash or a kill from the
/// Task Manager the Python server would keep running. A job object with
/// KILL_ON_JOB_CLOSE is what Windows provides for exactly this - when the last
/// handle goes, however it goes, the system takes the children with it.
/// (Same construction as in MutexxVocalRemover.)
#[cfg(windows)]
mod child_binding {
    use std::sync::OnceLock;

    use windows_sys::Win32::Foundation::HANDLE;
    use windows_sys::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    use windows_sys::Win32::System::Threading::{OpenProcess, PROCESS_SET_QUOTA, PROCESS_TERMINATE};

    struct Handle(HANDLE);
    // The handle is only held, never used across threads.
    unsafe impl Send for Handle {}
    unsafe impl Sync for Handle {}

    static JOB: OnceLock<Option<Handle>> = OnceLock::new();

    fn job() -> Option<HANDLE> {
        JOB.get_or_init(|| unsafe {
            let job = CreateJobObjectW(std::ptr::null(), std::ptr::null());
            if job.is_null() {
                return None;
            }
            let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            let ok = SetInformationJobObject(
                job,
                JobObjectExtendedLimitInformation,
                &info as *const _ as *const _,
                std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
            );
            if ok == 0 {
                return None;
            }
            Some(Handle(job))
        })
        .as_ref()
        .map(|h| h.0)
    }

    pub fn attach(pid: u32) -> bool {
        let Some(job) = job() else { return false };
        unsafe {
            let process = OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, 0, pid);
            if process.is_null() {
                return false;
            }
            let ok = AssignProcessToJobObject(job, process);
            windows_sys::Win32::Foundation::CloseHandle(process);
            ok != 0
        }
    }
}

#[derive(Default)]
struct Server {
    child: Mutex<Option<Child>>,
    port: Mutex<u16>,
}

/// The update found at start, held until the user decides in the app.
#[derive(Default)]
struct Updates {
    pending: Mutex<Option<Update>>,
    installing: AtomicBool,
}

/// `%LOCALAPPDATA%\Mutexx Production\Mutexx Advertiser` - the same folder the
/// Python side picks on its own (`core._home`). Set explicitly anyway, so the
/// two can never disagree.
fn data_dir() -> PathBuf {
    let base = std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    base.join("Mutexx Production").join("Mutexx Advertiser")
}

fn log_path() -> PathBuf {
    data_dir().join("logs").join("server.log")
}

fn free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .and_then(|listener| listener.local_addr())
        .map(|addr| addr.port())
        .unwrap_or(8777)
}

/// The last lines of the server log - what the start screen shows when Python
/// gives up, instead of a bare "could not start".
fn log_tail() -> String {
    let Ok(mut file) = File::open(log_path()) else { return String::new() };
    let length = file.metadata().map(|m| m.len()).unwrap_or(0);
    let _ = file.seek(SeekFrom::Start(length.saturating_sub(2000)));
    let mut text = String::new();
    let _ = file.read_to_string(&mut text);
    text
}

fn start_server(app: &tauri::AppHandle) -> Result<u16, String> {
    let resources = app
        .path()
        .resource_dir()
        .map_err(|e| format!("resource folder not found: {e}"))?;
    let python = resources.join("python").join("python.exe");
    let script = resources.join("app").join("start.py");
    if !python.is_file() || !script.is_file() {
        return Err(format!(
            "The bundled runtime is missing.\n{}\n{}",
            python.display(),
            script.display()
        ));
    }

    let home = data_dir();
    let logs = home.join("logs");
    fs::create_dir_all(&logs).map_err(|e| format!("{}: {e}", logs.display()))?;
    let log = log_path();
    if log.exists() {
        let _ = fs::rename(&log, logs.join("server.previous.log"));
    }
    let out = File::create(&log).map_err(|e| format!("{}: {e}", log.display()))?;
    let err = out.try_clone().map_err(|e| e.to_string())?;

    let port = free_port();
    let mut command = Command::new(&python);
    command
        .arg("-u")
        .arg(&script)
        .current_dir(resources.join("app"))
        .env("MUTEXX_ADVERTISER_HOME", &home)
        .env("MUTEXX_ADVERTISER_PORT", port.to_string())
        .env("MUTEXX_ADVERTISER_NO_BROWSER", "1")
        .env("MUTEXX_ADVERTISER_DESKTOP", "1")
        // Program Files is read-only for the user; without this Python tries to
        // write __pycache__ next to every module on every start.
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .env("PYTHONUTF8", "1")
        .stdin(Stdio::null())
        .stdout(Stdio::from(out))
        .stderr(Stdio::from(err));
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);

    let child = command
        .spawn()
        .map_err(|e| format!("Python could not be started: {e}"))?;
    #[cfg(windows)]
    child_binding::attach(child.id());

    let state = app.state::<Server>();
    *state.child.lock().unwrap() = Some(child);
    *state.port.lock().unwrap() = port;
    Ok(port)
}

/// Waits for the server, then points the window at it. Runs on its own thread:
/// the window is already up and showing the start screen meanwhile.
fn wait_and_show(app: tauri::AppHandle, window: WebviewWindow, port: u16) {
    std::thread::spawn(move || {
        let address: SocketAddr = ([127, 0, 0, 1], port).into();
        let started = Instant::now();
        loop {
            if TcpStream::connect_timeout(&address, Duration::from_millis(300)).is_ok() {
                if let Ok(url) = Url::parse(&format!("http://127.0.0.1:{port}/")) {
                    let _ = window.navigate(url);
                }
                return;
            }
            let exited = app
                .state::<Server>()
                .child
                .lock()
                .unwrap()
                .as_mut()
                .map(|child| matches!(child.try_wait(), Ok(Some(_))))
                .unwrap_or(true);
            if exited || started.elapsed() > START_TIMEOUT {
                let detail = serde_json::to_string(&log_tail()).unwrap_or_default();
                let _ = window.eval(&format!("window.showStartError({detail})"));
                return;
            }
            std::thread::sleep(Duration::from_millis(250));
        }
    });
}

/// Is this address part of the app - the start screen or the local server?
fn is_inside(url: &Url, port: u16) -> bool {
    match url.scheme() {
        "tauri" => true,
        "http" | "https" => match url.host_str() {
            Some("tauri.localhost") => true,
            Some("127.0.0.1") | Some("localhost") => url.port() == Some(port),
            _ => false,
        },
        "about" | "data" => true,
        _ => false,
    }
}

/// Everything else opens in the user's browser - where they are signed in to
/// Reddit, Lemmy or the forum. Posting from inside the app would mean signing in
/// there a second time, and the last click belongs in their own browser anyway.
fn open_outside(url: &Url) {
    if matches!(url.scheme(), "http" | "https" | "mailto") {
        let _ = tauri_plugin_opener::open_url(url.as_str(), None::<&str>);
    }
}

// ---------------------------------------------------------------------------
// Updates, shown inside the app
// ---------------------------------------------------------------------------
//
// The app itself is a page from the local Python server - a remote origin as far
// as Tauri is concerned, deliberately without access to Tauri's IPC. So the two
// talk through the two channels a shell has over any page anyway:
//
//   shell -> page   eval(): `window.mutexxDesktop.update({...})` and friends;
//   page  -> shell  a navigation to /__desktop/... on the app's own address. It is
//                   caught in on_navigation and never reaches the server, and only
//                   the app's own page can navigate this window.
//
// The page draws the update card in the app's own style. Nothing here opens a
// native dialog.

/// Runs a script in the app page. Payloads are JSON, never pasted strings.
fn tell_page(app: &tauri::AppHandle, script: String) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.eval(&format!("window.mutexxDesktop && {script}"));
    }
}

fn announce(app: &tauri::AppHandle, update: &Update) {
    let info = serde_json::json!({
        "version": update.version,
        "current": update.current_version,
        "notes": update.body.clone().unwrap_or_default(),
    });
    tell_page(app, format!("window.mutexxDesktop.update({info})"));
}

/// Quietly a few seconds after the start; at once when the user asks in Settings.
fn check_for_update(app: tauri::AppHandle, asked: bool) {
    std::thread::spawn(move || {
        if !asked {
            std::thread::sleep(Duration::from_secs(4));
        }
        let result = match app.updater() {
            Ok(updater) => tauri::async_runtime::block_on(updater.check()),
            Err(error) => Err(error),
        };
        match result {
            Ok(Some(update)) => {
                announce(&app, &update);
                *app.state::<Updates>().pending.lock().unwrap() = Some(update);
            }
            Ok(None) if asked => tell_page(&app, "window.mutexxDesktop.upToDate()".into()),
            Err(error) if asked => {
                let message = serde_json::to_string(&error.to_string()).unwrap_or_default();
                tell_page(&app, format!("window.mutexxDesktop.failed({message})"));
            }
            _ => {}
        }
    });
}

/// Download with progress in the card, then hand over to the installer. Windows
/// asks for administrator rights at that point - the app lives under Program
/// Files - and the installer brings the app back up afterwards.
fn install_update(app: tauri::AppHandle) {
    let state = app.state::<Updates>();
    let Some(update) = state.pending.lock().unwrap().clone() else { return };
    if state.installing.swap(true, Ordering::SeqCst) {
        return;
    }
    std::thread::spawn(move || {
        let mut received: u64 = 0;
        let mut last = Instant::now() - Duration::from_secs(1);
        let progress_app = app.clone();
        let download = tauri::async_runtime::block_on(update.download(
            move |chunk, total| {
                received += chunk as u64;
                // A few updates a second are plenty; one per chunk would flood eval.
                if last.elapsed() >= Duration::from_millis(120) {
                    last = Instant::now();
                    let total = total.map(|t| t.to_string()).unwrap_or_else(|| "null".into());
                    tell_page(&progress_app, format!("window.mutexxDesktop.progress({received},{total})"));
                }
            },
            || {},
        ));
        let bytes = match download {
            Ok(bytes) => bytes,
            Err(error) => {
                let message = serde_json::to_string(&error.to_string()).unwrap_or_default();
                tell_page(&app, format!("window.mutexxDesktop.failed({message})"));
                app.state::<Updates>().installing.store(false, Ordering::SeqCst);
                return;
            }
        };
        tell_page(&app, "window.mutexxDesktop.installing()".into());
        // Give the page a moment to say so, then free the files the installer
        // is about to replace.
        std::thread::sleep(Duration::from_millis(600));
        stop_server(&app);
        match update.install(bytes) {
            Ok(()) => app.restart(),
            Err(error) => {
                // The server is gone; the start screen is the only thing left to
                // show the reason on. A restart brings the old version back up.
                let _ = fs::write(log_path(), format!("Update failed: {error}"));
                app.restart();
            }
        }
    });
}

/// The page's way of asking the shell for something. See the block comment above.
fn desktop_request(app: &tauri::AppHandle, url: &Url, port: u16) -> bool {
    let ours = matches!(url.host_str(), Some("127.0.0.1") | Some("localhost"))
        && url.port() == Some(port);
    if !ours || !url.path().starts_with("/__desktop/") {
        return false;
    }
    match url.path() {
        "/__desktop/update/install" => install_update(app.clone()),
        "/__desktop/update/check" => check_for_update(app.clone(), true),
        _ => {}
    }
    true
}

fn stop_server(app: &tauri::AppHandle) {
    if let Some(state) = app.try_state::<Server>() {
        if let Some(mut child) = state.child.lock().unwrap().take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        // A second instance would start a second server and a second sync on the
        // same data. Whoever starts the app twice means the window already open.
        // Must come before all other plugins.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(Server::default())
        .manage(Updates::default())
        .setup(|app| {
            let port = match start_server(app.handle()) {
                Ok(port) => port,
                Err(detail) => {
                    // Still open the window, so the user sees why.
                    let _ = fs::create_dir_all(data_dir().join("logs"));
                    let _ = fs::write(log_path(), &detail);
                    0
                }
            };

            // The window is built here rather than from the configuration, for one
            // reason: WebView2's data folder. Left alone it lands in
            // %LOCALAPPDATA%\<identifier>\EBWebView - a second folder next to
            // "Mutexx Production\Mutexx Advertiser", which the folder rule exists
            // to prevent.
            let config = app
                .config()
                .app
                .windows
                .iter()
                .find(|w| w.label == "main")
                .cloned()
                .ok_or("window configuration 'main' missing in tauri.conf.json")?;
            let handle = app.handle().clone();
            let load_handle = app.handle().clone();
            let window = WebviewWindowBuilder::from_config(app.handle(), &config)?
                .data_directory(data_dir().join("webview"))
                .on_navigation(move |url| {
                    if desktop_request(&handle, url, port) {
                        return false;
                    }
                    if is_inside(url, port) {
                        return true;
                    }
                    open_outside(url);
                    false
                })
                // A reload of the page forgets what it was told - tell it again.
                .on_page_load(move |_window, payload| {
                    let ours = payload.url().port() == Some(port);
                    if ours && matches!(payload.event(), PageLoadEvent::Finished) {
                        if let Some(update) = load_handle.state::<Updates>().pending.lock().unwrap().as_ref() {
                            announce(&load_handle, update);
                        }
                    }
                })
                // window.open() - the posting assistant opens submit forms this
                // way. A second app window would have none of the user's logins.
                .on_new_window(|url, _features| {
                    open_outside(&url);
                    tauri::webview::NewWindowResponse::Deny
                })
                .build()?;

            if port == 0 {
                let detail = serde_json::to_string(&log_tail()).unwrap_or_default();
                let script = format!("window.showStartError({detail})");
                let window_for_error = window.clone();
                std::thread::spawn(move || {
                    std::thread::sleep(Duration::from_millis(600));
                    let _ = window_for_error.eval(&script);
                });
            } else {
                wait_and_show(app.handle().clone(), window, port);
            }

            check_for_update(app.handle().clone(), false);
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("the window could not be opened");

    app.run(|handle, event| {
        if let RunEvent::Exit = event {
            stop_server(handle);
        }
    });
}
