using System.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using OBDInsightBot.Models;

namespace OBDInsightBot.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        private readonly ApplicationDbContext _context;


        public HomeController(ILogger<HomeController> logger, ApplicationDbContext context)
        {
            _logger = logger;
            _context = context;
        }

        public async Task<IActionResult> Index()
        {
            // Checks the database is connected.
            bool dbConnected;

            try
            {
                dbConnected = _context.Database.CanConnect();
            }
            catch
            {
                dbConnected = false;
            }
            ViewBag.dbConnected = dbConnected;


            List<BlogPost> AllBlogPosts = await _context.BlogPosts.ToListAsync();
            ViewBag.blogPosts = AllBlogPosts;

            return View();
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
