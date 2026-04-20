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
    public class BlogsController : Controller
    {
        private readonly ApplicationDbContext _context;

        public BlogsController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET: BlogPosts
        public async Task<IActionResult> Index()
        {
            return View(await _context.BlogPosts.ToListAsync());
        }

        [HttpGet("/Blog/Post")]
        [HttpGet("/Blog/Post/{Id}")]
        public async Task<IActionResult> Article(Guid? Id)
        {
            if(Id == null)
            {
                return RedirectToAction("Index");
            }

            // finds the article
            BlogPost? ThisArticle = await _context.BlogPosts.FirstOrDefaultAsync(B => B.Id == Id) ?? null;
            if (ThisArticle == null)
            {
                return RedirectToAction("Index");
            }

            List<BlogItem> itemforBlog = await _context.BlogItems.Where(B => B.BlogPostId == Id).OrderBy(B => B.PositionInBlog).ToListAsync();
            ViewBag.thisBlogItems = itemforBlog;


            return View(ThisArticle);
        }




        [HttpGet("Manage")]
        public async Task<IActionResult> Admin()
        {
            List<BlogPost> blogs = await _context.BlogPosts.ToListAsync();
            ViewBag.posts = blogs;
            List<SingleUse> analytics = await _context.SignleUses.ToListAsync();
            ViewBag.single = analytics;


            return View();
        }

        [HttpGet("Manage/Blogs")]
        public async Task<IActionResult> ControlBlogs()
        {
            return View(await _context.BlogPosts.ToListAsync());
        }

        #region Details and items
        // GET: BlogPosts/Details/5
        public async Task<IActionResult> Details(Guid? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var blogPost = await _context.BlogPosts
                .FirstOrDefaultAsync(m => m.Id == id);
            if (blogPost == null)
            {
                return NotFound();
            }


            List<BlogItem> itemforBlog = await _context.BlogItems.Where(B => B.BlogPostId == id).OrderBy(B => B.PositionInBlog).ToListAsync();
            ViewBag.thisBlogItems = itemforBlog;

            return View(blogPost);
        }


        public async Task<IActionResult> AddBlogItem(Guid BlogID, Guid? id)
        {
            BlogPost? BP = await _context.BlogPosts.FirstOrDefaultAsync(b => b.Id == BlogID) ?? null;
            if (BP == null)
                return BadRequest("Couldnt Find blog post");


            ViewBag.BlogPost = BP;
            // Creating a new BlogItem
            if (id == null)
            {
                return View(new BlogItem()
                {
                    BlogPostId = BlogID
                });
            }

            // Editing an existing BlogItem
            var blogitem = await _context.BlogItems
                .FirstOrDefaultAsync(m => m.Id == id);

            if (blogitem == null)
            {
                // Could not find item, return a new one assigned to BlogID
                return View(new BlogItem()
                {
                    BlogPostId = BlogID
                });

            }

            return View(blogitem);
        }

        public async Task<IActionResult> AddBlogItemConfirm(BlogItem model)
        {
            BlogPost? BP = await _context.BlogPosts.FirstOrDefaultAsync(b => b.Id == model.BlogPostId) ?? null;
            if (BP == null)
                return BadRequest("Couldnt Find blog post");


            Debug.WriteLine($"  Passed in ID is: {model.BlogPostId}");

            // ------------------------------
            // 1. Validate incoming model
            // ------------------------------
            ModelState.Remove(nameof(BlogItem.Id));
            ModelState.Remove(nameof(BlogItem.BlogPost));

            if (!ModelState.IsValid)
            {
                // Return the same AddBlogItem view with validation messages

                Debug.WriteLine("Model state is invallied: ");

                foreach (var entry in ModelState)
                {
                    if (entry.Value.Errors.Any())
                    {
                        Debug.WriteLine($"Property: {entry.Key}");
                        foreach (var error in entry.Value.Errors)
                        {
                            Debug.WriteLine($"  Error: {error.ErrorMessage}");
                        }
                    }
                }

                return View("AddBlogItem", model);
            }

            // ------------------------------
            // 2. Save to DB
            // ------------------------------
            try
            {
                // If Id == default, it's a new item. Otherwise, update existing
                
                    _context.BlogItems.Add(model);
                

                await _context.SaveChangesAsync();
            }
            catch
            {
                // If saving fails, show form again with error
                ModelState.AddModelError("", "There was a problem saving the blog item.");
                return View("AddBlogItem", model);
            }

            // ------------------------------
            // 3. Success → redirect to Blog Details page
            // ------------------------------
            return RedirectToAction(
                nameof(Details),          // Action
                new { id = model.BlogPostId }
            );
        }

        public async Task<IActionResult> RemoveBlogItemConfirmed(Guid BlogItemID)
        {
            BlogItem? BI = await _context.BlogItems.FirstOrDefaultAsync(I => I.Id == BlogItemID) ?? null;
            if (BI == null) return BadRequest("Unable to find item to remove");


            _context.Remove(BI);
            _context.SaveChangesAsync();

            return RedirectToAction("Details", new { id = BI.BlogPostId });

        }

        #endregion









        // GET: BlogPosts/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: BlogPosts/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("WrittenAt,Title,MiniDescription,Content,PostedAt,IsHidden,PathForFeaturedImage")] BlogPost blogPost)
        {
            if (ModelState.IsValid)
            {
                _context.Add(blogPost);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            return View(blogPost);
        }



        // GET: BlogPosts/Edit/5
        public async Task<IActionResult> Edit(Guid? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var blogPost = await _context.BlogPosts.FindAsync(id);
            if (blogPost == null)
            {
                return NotFound();
            }
            return View(blogPost);
        }

        // POST: BlogPosts/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.



        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(Guid id, [Bind("Id,WrittenAt,Title,MiniDescription,Content,PostedAt,IsHidden,PathForFeaturedImage")] BlogPost blogPost)
        {
            Debug.WriteLine($"  In edit methord");

            //if (id != blogPost.Id)
            //{
            //    Debug.WriteLine($"  ID's dont match");

            //    return NotFound();
            //}

            ModelState.Remove(nameof(BlogItem.BlogPost));
            if (ModelState.IsValid)
            {


                try
                {
                    BlogPost thisBP = await _context.BlogPosts.FirstOrDefaultAsync(B => B.Id == id);
                    if (thisBP == null) { return BadRequest("Selected Blog not found"); }

                    thisBP.WrittenAt = DateTime.UtcNow;
                    thisBP.Title = blogPost.Title;
                    thisBP.MiniDescription = blogPost.MiniDescription;
                    thisBP.PathForFeaturedImage = blogPost.PathForFeaturedImage;
                    thisBP.IsHidden = blogPost.IsHidden;
                    thisBP.Content = blogPost.Content;
                    thisBP.WrittenAt = blogPost.WrittenAt;



                    _context.Update(thisBP);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!BlogPostExists(blogPost.Id))
                    {
                        return NotFound();
                    }
                    else
                    {
                        throw;
                    }
                }
                return RedirectToAction(nameof(Index));
            }
            else
            {
                foreach (var entry in ModelState)
                {
                    if (entry.Value.Errors.Any())
                    {
                        Debug.WriteLine($"Property: {entry.Key}");
                        foreach (var error in entry.Value.Errors)
                        {
                            Debug.WriteLine($"  Error: {error.ErrorMessage}");
                        }
                    }
                }
            }
                return View(blogPost);
        }

        // GET: BlogPosts/Delete/5
        public async Task<IActionResult> Delete(Guid? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var blogPost = await _context.BlogPosts
                .FirstOrDefaultAsync(m => m.Id == id);



            if (blogPost == null)
            {
                return NotFound();
            }

            return View(blogPost);
        }

        // POST: BlogPosts/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(Guid id)
        {
            var blogPost = await _context.BlogPosts.FindAsync(id);
            if (blogPost != null)
            {
                List<BlogItem> items = await _context.BlogItems.Where(I => I.BlogPostId == id).ToListAsync();

                _context.BlogItems.RemoveRange(items);

                _context.BlogPosts.Remove(blogPost);

            }

            await _context.SaveChangesAsync();
            return RedirectToAction("ControlBlogs");
        }

        internal bool BlogPostExists(Guid id)
        {
            return _context.BlogPosts.Any(e => e.Id == id);
        }
    }
}
