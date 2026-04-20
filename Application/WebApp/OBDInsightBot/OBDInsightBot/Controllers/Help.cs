using Microsoft.AspNetCore.Mvc;

namespace OBDInsightBot.Controllers
{
    public class Help : Controller
    {
        public IActionResult Index()
        {
            return View();
        }

        public IActionResult Example() { return View(); }
    }
}
