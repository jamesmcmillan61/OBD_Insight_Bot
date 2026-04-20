using Microsoft.AspNetCore.Mvc;

namespace OBDInsightBot.Controllers
{
    public class SettingsController : Controller
    {
        public IActionResult Index()
        {
            return View();
        }
    }
}
