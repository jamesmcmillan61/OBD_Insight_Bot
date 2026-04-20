using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Microsoft.VisualStudio.Web.CodeGenerators.Mvc.Templates.BlazorIdentity.Pages;
using OBDInsightBot.Models;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace OBDInsightBot.Controllers
{
    public class Analytics : Controller
    {
        private readonly ApplicationDbContext _context;

        public Analytics(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<IActionResult> Index()
        {
            List<SingleUse> uses = await _context.SignleUses.ToListAsync();

            return View(uses);
        }

        public async Task<IActionResult> Topics()
        {



            return View(await _context.TopicAnalytics.ToListAsync());
        }
    }
}
