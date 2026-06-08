//! Rust screen capture backend — sub-10ms JPEG frames on Linux/macOS/Windows.

use image::imageops::FilterType;
use image::{DynamicImage, ImageBuffer, Rgba};
use jpeg_encoder::{ColorType, Encoder};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::io::Cursor;
use std::time::{SystemTime, UNIX_EPOCH};
use xcap::Monitor;

type RgbaImage = ImageBuffer<Rgba<u8>, Vec<u8>>;

fn primary_monitor() -> PyResult<Monitor> {
    Monitor::all()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?
        .into_iter()
        .next()
        .ok_or_else(|| pyo3::exceptions::PyRuntimeError::new_err("No monitor found"))
}

fn rgba_to_jpeg(img: &RgbaImage, quality: u8) -> PyResult<Vec<u8>> {
    let rgb: ImageBuffer<image::Rgb<u8>, Vec<u8>> = ImageBuffer::from_fn(img.width(), img.height(), |x, y| {
        let p = img.get_pixel(x, y);
        image::Rgb([p[0], p[1], p[2]])
    });
    let mut buf = Vec::with_capacity((img.width() * img.height() / 4) as usize);
    let mut cursor = Cursor::new(&mut buf);
    let enc = Encoder::new(&mut cursor, quality);
    enc.encode(
        rgb.as_raw(),
        rgb.width() as u16,
        rgb.height() as u16,
        ColorType::Rgb,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(buf)
}

#[pyfunction]
#[pyo3(signature = (quality=55, scale=0.75, region=None))]
fn capture_jpeg(quality: u8, scale: f32, region: Option<(u32, u32, u32, u32)>) -> PyResult<Vec<u8>> {
    let monitor = primary_monitor()?;
    let raw = monitor
        .capture_image()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let mut img = DynamicImage::ImageRgba8(raw);

    if let Some((x, y, w, h)) = region {
        img = img.crop_imm(x, y, w, h);
    }

    let scale = scale.clamp(0.1, 1.0);
    if scale < 1.0 {
        let nw = ((img.width() as f32) * scale).max(1.0) as u32;
        let nh = ((img.height() as f32) * scale).max(1.0) as u32;
        img = DynamicImage::ImageRgba8(image::imageops::resize(
            &img.to_rgba8(),
            nw,
            nh,
            FilterType::Triangle,
        ));
    }

    rgba_to_jpeg(&img.to_rgba8(), quality.clamp(20, 95))
}

#[pyfunction]
#[pyo3(signature = (quality=55, scale=0.75, region=None))]
fn capture_jpeg_scaled(quality: u8, scale: f32, region: Option<(u32, u32, u32, u32)>) -> PyResult<(Vec<u8>, u32, u32)> {
    let monitor = primary_monitor()?;
    let full_w = monitor.width().unwrap_or(1920);
    let full_h = monitor.height().unwrap_or(1080);
    let data = capture_jpeg(quality, scale, region)?;
    let scale = scale.clamp(0.1, 1.0);
    let out_w = if region.is_some() {
        region.unwrap().2
    } else {
        ((full_w as f32) * scale).max(1.0) as u32
    };
    let out_h = if region.is_some() {
        region.unwrap().3
    } else {
        ((full_h as f32) * scale).max(1.0) as u32
    };
    Ok((data, out_w, out_h))
}

#[pyfunction]
fn screen_size() -> PyResult<(u32, u32)> {
    let m = primary_monitor()?;
    Ok((m.width().unwrap_or(1920), m.height().unwrap_or(1080)))
}

#[pyfunction]
fn check_permissions(py: Python<'_>) -> PyResult<Py<PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("platform", std::env::consts::OS)?;
    dict.set_item("arch", std::env::consts::ARCH)?;

    let capture_ok = Monitor::all()
        .ok()
        .and_then(|m| m.into_iter().next())
        .and_then(|mon| mon.capture_image().ok())
        .is_some();
    dict.set_item("screen_capture", capture_ok)?;
    dict.set_item("mouse_keyboard", true)?; // validated at Python layer
    dict.set_item("backend", "rust")?;

    let hints: Vec<&str> = match std::env::consts::OS {
        "macos" => vec![
            "System Settings → Privacy → Screen Recording: allow terminal/daffodil-kit",
            "System Settings → Privacy → Accessibility: allow for mouse/keyboard",
        ],
        "linux" => vec![
            "Wayland: approve ScreenCast portal when prompted",
            "X11: set DISPLAY; add user to input group if needed",
        ],
        "windows" => vec![
            "Run on interactive desktop session (not headless SSH)",
        ],
        _ => vec![],
    };
    dict.set_item("hints", hints)?;
    dict.set_item("ready", capture_ok)?;
    dict.set_item(
        "timestamp",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs_f64())
            .unwrap_or(0.0),
    )?;
    Ok(dict.into())
}

#[pyfunction]
fn native_available() -> bool {
    true
}

#[pymodule]
fn daffodil_kit_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(capture_jpeg, m)?)?;
    m.add_function(wrap_pyfunction!(capture_jpeg_scaled, m)?)?;
    m.add_function(wrap_pyfunction!(screen_size, m)?)?;
    m.add_function(wrap_pyfunction!(check_permissions, m)?)?;
    m.add_function(wrap_pyfunction!(native_available, m)?)?;
    Ok(())
}
