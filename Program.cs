using NetTrafficMonitor;
using System;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    private static string configPath = Path.Combine(
    AppDomain.CurrentDomain.BaseDirectory,
    "config.json"
);
    private static Config config = new Config();
    private static readonly object configLock = new object();

    private static string biosUuid;

    static async Task Main(string[] args)
    {
        // BIOS UUID olish
        biosUuid = GetBiosUuid();
        if (biosUuid == null)
        {
            Console.WriteLine("⚠️ BIOS UUID topilmadi, POST qilinmaydi.");
            return;
        }
        Console.WriteLine($"✅ BIOS UUID (host): {biosUuid}");

        // Configni dastlabki yuklash
        LoadConfig();

        // Faylni kuzatuvchi ishga tushirish
        WatchConfigFile();

        // TrafficCollector sozlash
        TrafficCollector.HostId = biosUuid;
        ApplyIgnoredIps();

        // Monitoring start
        TrafficCollector.Start();
        Console.WriteLine("🚀 Monitoring started...");

        using var httpClient = new HttpClient();

        while (true)
        {
            int delaySeconds;
            string backendUrl;
            string status;

            lock (configLock)
            {
                delaySeconds = config.DelaySeconds;
                backendUrl = config.BackendUrl;
                status = config.Status;
            }

            await Task.Delay(delaySeconds * 1000);

            // Traffic olish
            string finalJson = TrafficCollector.GetTrafficInfo(delaySeconds);
            Console.WriteLine(finalJson);

            // Agar status "run" bo'lsa POST qilamiz
            if (status?.ToLower() == "run")
            {
                try
                {
                    using var content = new StringContent(finalJson, Encoding.UTF8, "application/json");
                    using var response = await httpClient.PostAsync(backendUrl, content);
                    Console.WriteLine($"🌐 POST status: {response.StatusCode}");
                    string errorMessage = await response.Content.ReadAsStringAsync();
                    if (!response.IsSuccessStatusCode)
                    {
                        Console.WriteLine($"❌ Xato: {response.ReasonPhrase}");
                        Console.WriteLine($"📩 Server javobi: {errorMessage}");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ POST error: {ex.Message}");
                }
            }
            else
            {
                Console.WriteLine("⏸️ Status 'stop' — POST qilinmayapti.");
            }
        }
    }

    /// <summary>
    /// Configni fayldan yuklash
    /// </summary>
    private static void LoadConfig()
    {
        try
        {
            if (!File.Exists(configPath))
            {
                Console.WriteLine("⚠️ config.json topilmadi!");
                return;
            }

            string json = File.ReadAllText(configPath);
            var newConfig = JsonSerializer.Deserialize<Config>(json);

            if (newConfig != null)
            {
                lock (configLock)
                {
                    config = newConfig;
                }

                Console.WriteLine("✅ Config yangilandi:");
                Console.WriteLine(json);

                ApplyIgnoredIps();
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Config yuklashda xato: {ex.Message}");
        }
    }

    /// <summary>
    /// Config faylini kuzatib turish
    /// </summary>
    private static void WatchConfigFile()
    {
        var watcher = new FileSystemWatcher(Path.GetDirectoryName(configPath) ?? ".", Path.GetFileName(configPath))
        {
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.Size
        };

        watcher.Changed += (s, e) =>
        {
            // Biros kutib olish (yangi yozilish tugaguncha)
            Thread.Sleep(500);
            LoadConfig();
        };

        watcher.EnableRaisingEvents = true;
    }

    /// <summary>
    /// Ignored IP larni Collector ga qo‘shish
    /// </summary>
    private static void ApplyIgnoredIps()
    {
        lock (configLock)
        {
            if (config.IgnoredIps != null)
            {
                foreach (var ip in config.IgnoredIps)
                {
                    TrafficCollector.AddIgnoredIp(ip);
                }
            }
        }
    }

    /// <summary>
    /// Windows da BIOS UUID olish (wmic bilan)
    /// </summary>
    private static string GetBiosUuid()
    {
        try
        {
            using var searcher = new ManagementObjectSearcher("SELECT UUID FROM Win32_ComputerSystemProduct");
            foreach (var obj in searcher.Get())
            {
                return obj["UUID"]?.ToString();
            }
        }
        catch
        {
            return null;
        }
        return null;
    }
}

/// <summary>
/// Config modeli
/// </summary>
public class Config
{
    public string BackendUrl { get; set; } = "http://94.141.85.114:4555/applications/applications/";
    public string[] IgnoredIps { get; set; } = new string[] { "127.0.0.1" };
    public int DelaySeconds { get; set; } = 5;
    public string Status { get; set; } = "run";
}