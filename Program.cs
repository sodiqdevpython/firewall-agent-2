using NetTrafficMonitor;
using System;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    static async Task Main()
    {
        // Ignor qilinadigan IP qo'shish (masalan localhost)
        TrafficCollector.AddIgnoredIp("127.0.0.1");

        // Collector ishga tushadi
        TrafficCollector.Start();
        Console.WriteLine("🚀 Monitoring started... (har 5 sekundda oxirgi 5 sekund)");

        // Har 5 sekundda JSON chiqarib borish
        while (true)
        {
            await Task.Delay(5000);
            string json = TrafficCollector.GetTrafficInfo(5);
            Console.WriteLine(json);
        }
    }
}
