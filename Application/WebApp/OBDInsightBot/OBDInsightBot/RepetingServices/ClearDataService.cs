// This is a service that runs every 30 minuites. It removes all corresponding data from chas that have not been used within the past 30 minuites.

using Microsoft.EntityFrameworkCore;
using OBDInsightBot.Models;
using System.Diagnostics;

namespace OBDInsightBot.RepetingServices
{
    public class ClearDataService : BackgroundService
    {
        private readonly IServiceScopeFactory _scopeFactory;
        private readonly ILogger<ClearDataService> _logger;

        public ClearDataService(
        IServiceScopeFactory scopeFactory,
        ILogger<ClearDataService> logger)
        {
            _scopeFactory = scopeFactory;
            _logger = logger;
        }




        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    using var scope = _scopeFactory.CreateScope();
                    var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

                    await RemoveOldDataAsync(context);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error while cleaning old data");
                }

                await Task.Delay(TimeSpan.FromMinutes(30), stoppingToken);
            }
        }





        private async Task RemoveOldDataAsync(ApplicationDbContext _context)
        {
            var cutoffTime = DateTime.Now.AddMinutes(-30);

            List<UserSession> oldUS = await _context.UserSessions
                .Where(us => us.lastUseTime < cutoffTime)
                .ToListAsync();

            foreach (UserSession us in oldUS)
            {
                var UOBDD = await _context.UserOBDDatas
                    .FirstOrDefaultAsync(d => d.UserSessionId == us.Id);

                if (UOBDD != null)
                    _context.UserOBDDatas.Remove(UOBDD);

                var selectedChats = await _context.UserChatItems
                    .Where(s => s.UserSessionId == us.Id)
                    .ToListAsync();

                if (selectedChats.Any())
                    _context.UserChatItems.RemoveRange(selectedChats);

                if (!string.IsNullOrEmpty(us.UploadedDataPath) &&
                    File.Exists(us.UploadedDataPath))
                {
                    try
                    {
                        File.Delete(us.UploadedDataPath);
                    }
                    catch (Exception ex)
                    {
                        // log but do not stop cleanup
                        Console.WriteLine($"File delete error: {ex.Message}");
                    }
                }
            }

            _context.UserSessions.RemoveRange(oldUS);
            await _context.SaveChangesAsync();
        }

    }
}