using Microsoft.Diagnostics.Tracing;
using Microsoft.Diagnostics.Tracing.Parsers;
using Microsoft.Diagnostics.Tracing.Parsers.Kernel;
using Microsoft.Diagnostics.Tracing.Session;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

namespace NetTrafficMonitor
{
    public static class TrafficCollector
    {
        private static readonly ConcurrentDictionary<int, ProcStats> stats = new();
        private static readonly HashSet<string> ignoredIps = new(StringComparer.OrdinalIgnoreCase);

        private static TraceEventSession session;
        private static CancellationTokenSource cts;

        /// <summary>
        /// Bir marta olingan host identifikatori (BIOS UUID) shu yerda saqlanadi.
        /// Program.cs ishga tushganda set qiladi.
        /// </summary>
        public static string HostId { get; set; } = "UNKNOWN-UUID";

        /// <summary>
        /// IP ni filterga qo'shish (masalan: 127.0.0.1 ni hisobga olmaslik).
        /// </summary>
        public static void AddIgnoredIp(string ip)
        {
            ignoredIps.Add(ip);
        }

        public static void Start()
        {
            if (session != null) return;
            if (TraceEventSession.IsElevated() == false)
                throw new Exception("Run as Administrator!");

            cts = new CancellationTokenSource();
            session = new TraceEventSession("NetMonSession");
            session.EnableKernelProvider(KernelTraceEventParser.Keywords.NetworkTCPIP);

            session.Source.Kernel.TcpIpRecv += data =>
            {
                HandleEvent(data.ProcessID, data.saddr.ToString(), data.sport, data.daddr.ToString(), data.dport, data.size, "Inbound");
            };

            session.Source.Kernel.TcpIpSend += data =>
            {
                HandleEvent(data.ProcessID, data.saddr.ToString(), data.sport, data.daddr.ToString(), data.dport, data.size, "Outbound");
            };

            Task.Run(() => session.Source.Process(), cts.Token);
        }

        public static void Stop()
        {
            try
            {
                cts?.Cancel();
                session?.Dispose();
            }
            catch { }
            finally
            {
                session = null;
            }
        }

        /// <summary>
        /// Oxirgi n sekunddagi trafikni JSON ko'rinishda qaytaradi (bulk list).
        /// </summary>
        public static string GetTrafficInfo(int lastSeconds = 5)
        {
            DateTime cutoff = DateTime.UtcNow.AddSeconds(-lastSeconds);
            var snapshot = new List<ProcStats>();

            foreach (var kv in stats)
            {
                var ps = kv.Value.CloneWithFilter(cutoff);
                // Faqat trafik bo'lgan yoki hech bo'lmasa obyekt ma'noli bo'lishi uchun qaytaramiz
                if (ps.Sent > 0 || ps.Received > 0 || ps.Connections.Count > 0)
                    snapshot.Add(ps);
            }

            return JsonSerializer.Serialize(snapshot, new JsonSerializerOptions
            {
                WriteIndented = true
            });
        }

        private static void HandleEvent(int pid, string srcIp, int srcPort, string dstIp, int dstPort, int size, string direction)
        {
            try
            {
                // Ignore list bo'yicha filter
                if (ignoredIps.Contains(srcIp) || ignoredIps.Contains(dstIp))
                    return;

                Process proc = null;
                try { proc = Process.GetProcessById(pid); } catch { }

                var ps = stats.GetOrAdd(pid, _ =>
                {
                    string exePath = "UNKNOWN";
                    try { exePath = proc?.MainModule?.FileName ?? "UNKNOWN"; } catch { }

                    return new ProcStats
                    {
                        Host = HostId,
                        Pid = pid,
                        Name = proc?.ProcessName ?? "UNKNOWN",
                        ExePath = exePath
                    };
                });

                ps.TotalBytes += size;
                if (direction == "Inbound") ps.Received += size;
                else ps.Sent += size;

                ps.Connections.Add(new ConnectionInfo
                {
                    Timestamp = DateTime.UtcNow,
                    Direction = direction,
                    Local = $"{srcIp}:{srcPort}",
                    Remote = $"{dstIp}:{dstPort}",
                    Bytes = size
                });
            }
            catch { }
        }
    }

    public class ProcStats
    {
        [JsonPropertyName("host")]
        public string Host { get; set; }

        [JsonPropertyName("pid")]
        public int Pid { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; }

        // JSONda "image_path" bo'lib chiqadi
        [JsonPropertyName("image_path")]
        public string ExePath { get; set; }

        [JsonPropertyName("sent")]
        public long Sent { get; set; }

        [JsonPropertyName("received")]
        public long Received { get; set; }

        // Hisob-kitob uchun, ammo JSONga chiqarmaymiz
        [JsonIgnore]
        public long TotalBytes { get; set; }

        // JSONda aynan "Connections" nomi bilan chiqsin (default shunday)
        public List<ConnectionInfo> Connections { get; set; } = new();

        // Filtering uchun
        public ProcStats CloneWithFilter(DateTime cutoff)
        {
            var clone = new ProcStats
            {
                Host = this.Host,
                Pid = this.Pid,
                Name = this.Name,
                ExePath = this.ExePath
            };

            foreach (var conn in this.Connections)
            {
                if (conn.Timestamp >= cutoff)
                {
                    clone.Connections.Add(conn);
                    clone.TotalBytes += conn.Bytes;
                    if (conn.Direction == "Inbound") clone.Received += conn.Bytes;
                    else clone.Sent += conn.Bytes;
                }
            }
            return clone;
        }
    }

    public class ConnectionInfo
    {
        public DateTime Timestamp { get; set; }
        public string Direction { get; set; }
        public string Local { get; set; }
        public string Remote { get; set; }
        public long Bytes { get; set; }
    }
}
