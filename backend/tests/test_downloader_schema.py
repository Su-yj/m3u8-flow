from app.schemas.services.downloader import DownloadInfo


def test_download_info_progress_handles_zero_segments():
    info = DownloadInfo(total_segments=0, downloaded_segments=0)
    assert info.progress == 0.0


def test_download_info_eta_uses_downloaded_duration_and_speed():
    info = DownloadInfo(
        total_segments=10,
        downloaded_segments=5,
        total_size=5000,
        total_duration=100.0,
        downloaded_duration=50.0,
    )
    # speed_monitor 直接写样本较繁琐，测试里覆写 current_speed 依赖对象更直观
    class _SpeedMonitor:
        current_speed = 100.0

    info.speed_monitor = _SpeedMonitor()  # type: ignore[assignment]
    # total_size / downloaded_duration = 100 bytes/s(duration)
    # remaining_duration = 50s -> remaining_bytes = 5000
    # eta = 5000 / 100 = 50s
    assert info.eta == 50.0


def test_download_info_eta_returns_none_when_no_effective_speed():
    info = DownloadInfo(
        total_segments=10,
        downloaded_segments=5,
        total_size=5000,
        total_duration=100.0,
        downloaded_duration=50.0,
    )

    class _SpeedMonitor:
        current_speed = 0.0

    info.speed_monitor = _SpeedMonitor()  # type: ignore[assignment]
    assert info.eta is None
