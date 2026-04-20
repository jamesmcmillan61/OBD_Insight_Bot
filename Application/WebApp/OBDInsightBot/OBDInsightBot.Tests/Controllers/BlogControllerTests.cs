using FluentAssertions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Moq;
using OBDInsightBot.Controllers;
using OBDInsightBot.Models;

namespace OBDInsightBot.Tests.Controllers;

public class BlogsControllerTests : IDisposable
{
    private readonly ApplicationDbContext _context;
    private readonly BlogsController _controller;

    public BlogsControllerTests()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        _context = new ApplicationDbContext(options);
        _controller = new BlogsController(_context);
    }

    public void Dispose()
    {
        _context.Dispose();
    }

    private Guid CreateBlogPost()
    {
        var post = new BlogPost
        {
            Title = "Test Blog",
            MiniDescription = "Test",
            Content = "Content",
            WrittenAt = DateTime.Now
        };

        _context.BlogPosts.Add(post);
        _context.SaveChanges();

        return post.Id;
    }

    #region Index&Articles

    [Fact]
    public async Task Index_ReturnsViewWithBlogPosts()
    {
        var id = CreateBlogPost();

        var result = await _controller.Index();

        var viewResult = result.Should().BeOfType<ViewResult>().Subject;
        var model = viewResult.Model.Should().BeAssignableTo<List<BlogPost>>().Subject;

        model.Count.Should().Be(1);
    }

    [Fact]
    public async Task Article_NullId_RedirectsToIndex()
    {
        var result = await _controller.Article(null);

        result.Should().BeOfType<RedirectToActionResult>()
            .Which.ActionName.Should().Be("Index");
    }

    [Fact]
    public async Task Article_InvalidId_RedirectsToIndex()
    {
        var result = await _controller.Article(Guid.NewGuid());

        result.Should().BeOfType<RedirectToActionResult>()
            .Which.ActionName.Should().Be("Index");
    }

    [Fact]
    public async Task Article_ValidId_ReturnsViewWithBlog()
    {
        var blogId = CreateBlogPost();

        // Add a BlogItem
        _context.BlogItems.Add(new BlogItem
        {
            BlogPostId = blogId,
            PositionInBlog = 1,
            contence = "Item" // <-- use your correct property
        });

        _context.SaveChanges();

        var result = await _controller.Article(blogId);

        var viewResult = result.Should().BeOfType<ViewResult>().Subject;

        // Check the model is the BlogPost
        var model = viewResult.Model.Should().BeOfType<BlogPost>().Subject;
        model.Id.Should().Be(blogId);

        // Access ViewBag safely as dynamic
        dynamic viewBag = _controller.ViewBag;
        var items = ((IEnumerable<BlogItem>)viewBag.thisBlogItems).ToList();

        items.Should().NotBeNull();
        items.Should().ContainSingle(i => i.contence == "Item");
    }

    #endregion

    #region Admin & Details


    [Fact]
    public async Task Details_NullId_ReturnsNotFound()
    {
        var result = await _controller.Details(null);

        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Details_InvalidId_ReturnsNotFound()
    {
        var result = await _controller.Details(Guid.NewGuid());

        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Details_ValidId_ReturnsViewWithBlogPostAndItems()
    {
        var blogId = CreateBlogPost();

        // Add a BlogItem
        _context.BlogItems.Add(new BlogItem
        {
            BlogPostId = blogId,
            PositionInBlog = 1,
            contence = "Item content"
        });
        _context.SaveChanges();

        var result = await _controller.Details(blogId);

        var viewResult = result.Should().BeOfType<ViewResult>().Subject;

        var model = viewResult.Model.Should().BeOfType<BlogPost>().Subject;
        model.Id.Should().Be(blogId);

        var items = viewResult.ViewData["thisBlogItems"] as List<BlogItem>;
        items.Should().NotBeNull();
        items.Should().ContainSingle(i => i.contence == "Item content");
    }

    #endregion

    #region Actions

    [Fact]
    public void Create_Get_ReturnsView()
    {
        var result = _controller.Create();

        result.Should().BeOfType<ViewResult>();
    }

    [Fact]
    public async Task Create_Post_ValidModel_SavesAndRedirects()
    {
        var model = new BlogPost
        {
            Title = "New Blog",
            MiniDescription = "Mini desc",
            Content = "Content",
            WrittenAt = DateTimeOffset.UtcNow,
            PostedAt = DateTimeOffset.UtcNow,
            IsHidden = false
        };

        var result = await _controller.Create(model);

        var redirect = result.Should().BeOfType<RedirectToActionResult>().Subject;
        redirect.ActionName.Should().Be("Index");

        _context.BlogPosts.Should().ContainSingle(b => b.Title == "New Blog");
    }

    [Fact]
    public async Task Create_Post_InvalidModel_ReturnsView()
    {
        var model = new BlogPost(); // Missing required fields

        _controller.ModelState.AddModelError("Title", "Required");

        var result = await _controller.Create(model);

        var view = result.Should().BeOfType<ViewResult>().Subject;
        view.Model.Should().Be(model);
    }

    [Fact]
    public async Task Edit_Get_NullId_ReturnsNotFound()
    {
        var result = await _controller.Edit(null);
        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Edit_Get_InvalidId_ReturnsNotFound()
    {
        var result = await _controller.Edit(Guid.NewGuid());
        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Edit_Get_ValidId_ReturnsViewWithBlogPost()
    {
        var blogId = CreateBlogPost();
        var result = await _controller.Edit(blogId);

        var view = result.Should().BeOfType<ViewResult>().Subject;
        var model = view.Model.Should().BeOfType<BlogPost>().Subject;
        model.Id.Should().Be(blogId);
    }

    [Fact]
    public async Task Edit_Post_ValidModel_UpdatesAndRedirects()
    {
        var blogId = CreateBlogPost();
        var model = new BlogPost
        {
            Id = blogId,
            Title = "Updated",
            MiniDescription = "Mini",
            Content = "Content",
            WrittenAt = DateTimeOffset.UtcNow,
            PostedAt = DateTimeOffset.UtcNow,
            IsHidden = false
        };

        var result = await _controller.Edit(blogId, model);

        var redirect = result.Should().BeOfType<RedirectToActionResult>().Subject;
        redirect.ActionName.Should().Be("Index");

        _context.BlogPosts.First(b => b.Id == blogId).Title.Should().Be("Updated");
    }

    [Fact]
    public async Task Edit_Post_InvalidModel_ReturnsView()
    {
        var blogId = CreateBlogPost();
        var model = new BlogPost { Id = blogId };
        _controller.ModelState.AddModelError("Title", "Required");

        var result = await _controller.Edit(blogId, model);

        var view = result.Should().BeOfType<ViewResult>().Subject;
        view.Model.Should().Be(model);
    }

    [Fact]
    public async Task Edit_Post_BlogNotFound_ReturnsBadRequest()
    {
        var model = new BlogPost
        {
            Id = Guid.NewGuid(),
            Title = "Nonexistent"
        };

        var result = await _controller.Edit(model.Id, model);

        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Delete_Get_NullId_ReturnsNotFound()
    {
        var result = await _controller.Delete(null);
        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Delete_Get_InvalidId_ReturnsNotFound()
    {
        var result = await _controller.Delete(Guid.NewGuid());
        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Delete_Get_ValidId_ReturnsView()
    {
        var blogId = CreateBlogPost();
        var result = await _controller.Delete(blogId);

        var view = result.Should().BeOfType<ViewResult>().Subject;
        var model = view.Model.Should().BeOfType<BlogPost>().Subject;
        model.Id.Should().Be(blogId);
    }

    [Fact]
    public async Task DeleteConfirmed_RemovesBlogAndRedirects()
    {
        var blogId = CreateBlogPost();

        var result = await _controller.DeleteConfirmed(blogId);

        var redirect = result.Should().BeOfType<RedirectToActionResult>().Subject;
        redirect.ActionName.Should().Be("ControlBlogs");

        _context.BlogPosts.Should().BeEmpty();
    }


    public class TestDbContext : ApplicationDbContext
    {
        public TestDbContext(DbContextOptions<ApplicationDbContext> options) : base(options) { }

        public override Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
        {
            throw new DbUpdateConcurrencyException();
        }
    }

    [Fact]
    public async Task Edit_BlogDoesNotExist_ReturnsBadRequest()
    {
        // Arrange: create a BlogPost ID that does NOT exist in the context
        var nonExistentBlogId = Guid.NewGuid();

        var blogPost = new BlogPost
        {
            Id = nonExistentBlogId,
            Title = "Test",
            MiniDescription = "Test",
            Content = "Test",
            WrittenAt = DateTime.UtcNow,
            PostedAt = DateTime.UtcNow
        };

        // Act
        var result = await _controller.Edit(nonExistentBlogId, blogPost);

        // Assert
        result.Should().BeOfType<BadRequestObjectResult>()
            .Which.Value.Should().Be("Selected Blog not found");
    }

    [Fact]
    public async Task Edit_DbUpdateConcurrencyException_BlogExists_ThrowsException()
    {
        // Arrange: use a TestDbContext that always throws on SaveChangesAsync
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        using var testContext = new TestDbContext(options);
        var controller = new BlogsController(testContext);

        var blogPost = new BlogPost
        {
            Title = "Test",
            MiniDescription = "Test",
            Content = "Test",
            WrittenAt = DateTime.UtcNow,
            PostedAt = DateTime.UtcNow
        };

        testContext.BlogPosts.Add(blogPost);
        testContext.SaveChanges();

        // Act & Assert
        await FluentActions.Invoking(() => controller.Edit(blogPost.Id, blogPost))
            .Should().ThrowAsync<DbUpdateConcurrencyException>();
    }
    #endregion

    #region Add Blogg & Confirm

    [Fact]
    public async Task AddBlogItem_NullBlog_ReturnsBadRequest()
    {
        var result = await _controller.AddBlogItem(Guid.NewGuid(), null);
        result.Should().BeOfType<BadRequestObjectResult>()
            .Which.Value.Should().Be("Couldnt Find blog post");
    }

    [Fact]
    public async Task AddBlogItem_NewItem_ReturnsViewWithNewBlogItem()
    {
        var blogId = CreateBlogPost();

        var result = await _controller.AddBlogItem(blogId, null);

        var view = result.Should().BeOfType<ViewResult>().Subject;
        var model = view.Model.Should().BeOfType<BlogItem>().Subject;
        model.BlogPostId.Should().Be(blogId);
    }

    [Fact]
    public async Task AddBlogItem_ExistingItem_ReturnsViewWithBlogItem()
    {
        var blogId = CreateBlogPost();

        var item = new BlogItem
        {
            BlogPostId = blogId,
            contence = "Test",
            PositionInBlog = 1
        };
        _context.BlogItems.Add(item);
        _context.SaveChanges();

        var result = await _controller.AddBlogItem(blogId, item.Id);

        var view = result.Should().BeOfType<ViewResult>().Subject;
        var model = view.Model.Should().BeOfType<BlogItem>().Subject;
        model.Id.Should().Be(item.Id);
    }

    [Fact]
    public async Task AddBlogItemConfirm_InvalidBlog_ReturnsBadRequest()
    {
        var item = new BlogItem { BlogPostId = Guid.NewGuid() };

        var result = await _controller.AddBlogItemConfirm(item);

        result.Should().BeOfType<BadRequestObjectResult>()
            .Which.Value.Should().Be("Couldnt Find blog post");
    }

    [Fact]
    public async Task AddBlogItemConfirm_InvalidModel_ReturnsViewWithModel()
    {
        var blogId = CreateBlogPost();
        var item = new BlogItem { BlogPostId = blogId };
        _controller.ModelState.AddModelError("contence", "Required");

        var result = await _controller.AddBlogItemConfirm(item);

        var view = result.Should().BeOfType<ViewResult>().Subject;
        view.ViewName.Should().Be("AddBlogItem");
        view.Model.Should().Be(item);
    }

    [Fact]
    public async Task AddBlogItemConfirm_ValidModel_AddsToDbAndRedirects()
    {
        var blogId = CreateBlogPost();
        var item = new BlogItem
        {
            BlogPostId = blogId,
            contence = "Test",
            PositionInBlog = 1
        };

        var result = await _controller.AddBlogItemConfirm(item);

        var redirect = result.Should().BeOfType<RedirectToActionResult>().Subject;
        redirect.ActionName.Should().Be(nameof(_controller.Details));
        redirect.RouteValues!["id"].Should().Be(blogId);

        _context.BlogItems.Should().ContainSingle(bi => bi.contence == "Test");
    }

    [Fact]
    public async Task RemoveBlogItemConfirmed_NonexistentItem_ReturnsBadRequest()
    {
        var result = await _controller.RemoveBlogItemConfirmed(Guid.NewGuid());

        result.Should().BeOfType<BadRequestObjectResult>()
            .Which.Value.Should().Be("Unable to find item to remove");
    }

    [Fact]
    public async Task RemoveBlogItemConfirmed_ExistingItem_RemovesAndRedirects()
    {
        var blogId = CreateBlogPost();
        var item = new BlogItem
        {
            BlogPostId = blogId,
            contence = "Test",
            PositionInBlog = 1
        };
        _context.BlogItems.Add(item);
        _context.SaveChanges();

        var result = await _controller.RemoveBlogItemConfirmed(item.Id);

        var redirect = result.Should().BeOfType<RedirectToActionResult>().Subject;
        redirect.ActionName.Should().Be("Details");
        redirect.RouteValues!["id"].Should().Be(blogId);

        _context.BlogItems.Should().BeEmpty();
    }

    [Fact]
    public void BlogPostExists_ReturnsTrueIfExists()
    {
        var blogId = CreateBlogPost();

        var result = _controller.BlogPostExists(blogId);

        result.Should().BeTrue();
    }

    [Fact]
    public void BlogPostExists_ReturnsFalseIfNotExists()
    {
        var result = _controller.BlogPostExists(Guid.NewGuid());

        result.Should().BeFalse();
    }

    #endregion 
}