using System;
using System.IO;

namespace UsurperRemake.Systems
{
    /// <summary>
    /// 1.2.8: the per-user data directory, shared by the local saves and the Online Play login file. Windows
    /// %APPDATA%\UsurperReloaded, otherwise $HOME/.local/share/UsurperReloaded (.NET reports macOS as Unix, so
    /// macOS lands there too; the Library branch is kept as it was so no save moves).
    /// </summary>
    public static class UserDataPaths
    {
        private const string AppName = "UsurperReloaded";

        /// <summary>
        /// v1.3.9: <see cref="Get"/> if this process can actually write there, otherwise the game's own
        /// folder. A process started with a token that cannot reach %APPDATA% (a sandboxed shell, a
        /// managed desktop, a locked-down profile) could read the path and be denied every write, which
        /// is how the AI settings were lost on every launch: the save succeeded nowhere and the load
        /// found nothing, silently.
        /// </summary>
        public static string Writable()
        {
            if (_writable != null) return _writable;

            string primary = Get();
            if (CanWrite(primary)) { _writable = primary; return primary; }

            string beside = AppDomain.CurrentDomain.BaseDirectory;
            if (CanWrite(beside))
            {
                DebugLogger.Instance.LogWarning("PATHS",
                    $"Cannot write to {primary}; using {beside} for settings instead.");
                _writable = beside;
                return beside;
            }

            DebugLogger.Instance.LogError("PATHS", $"Neither {primary} nor {beside} is writable.");
            _writable = primary;
            return primary;
        }

        private static string? _writable;

        private static bool CanWrite(string directory)
        {
            try
            {
                Directory.CreateDirectory(directory);
                string probe = Path.Combine(directory, ".write-probe");
                File.WriteAllText(probe, "ok");
                File.Delete(probe);
                return true;
            }
            catch
            {
                return false;
            }
        }

        public static string Get()
        {
            if (Environment.OSVersion.Platform == PlatformID.Win32NT)
            {
                return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), AppName);
            }
            else if (Environment.OSVersion.Platform == PlatformID.Unix)
            {
                var home = Environment.GetEnvironmentVariable("HOME");
                return Path.Combine(home ?? "/tmp", ".local", "share", AppName);
            }
            else
            {
                var home = Environment.GetEnvironmentVariable("HOME");
                return Path.Combine(home ?? "/tmp", "Library", "Application Support", AppName);
            }
        }
    }
}
