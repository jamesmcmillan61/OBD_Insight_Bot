using FluentAssertions;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Moq;
using OBDInsightBot.Controllers;
using OBDInsightBot.Models;
using OBDInsightBot.Services;

namespace OBDInsightBot.Tests.Controllers;

public class ChatControllerTests : IDisposable
{
    private readonly ApplicationDbContext _context;
    private readonly ChatbotApiService _apiService;
    private readonly ChatController _controller;
    private readonly string _tempDir;

    public ChatControllerTests()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;
        _context = new ApplicationDbContext(options);

        var mockLogger = new Mock<ILogger<ChatbotApiService>>();
        var httpClient = new HttpClient(new Helpers.MockHttpMessageHandler(
            System.Net.HttpStatusCode.OK, "{}"))
        {
            BaseAddress = new Uri("http://localhost:8000")
        };
        _apiService = new ChatbotApiService(httpClient, mockLogger.Object);
        _controller = new ChatController(_context, _apiService);

        _tempDir = Path.Combine(Path.GetTempPath(), "obd_test_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_tempDir);
    }

    public void Dispose()
    {
        _context.Dispose();
        if (Directory.Exists(_tempDir))
        {
            Directory.Delete(_tempDir, true);
        }
    }

    private string CreateTempCsvFile(string content)
    {
        var filePath = Path.Combine(_tempDir, $"{Guid.NewGuid()}.csv");
        File.WriteAllText(filePath, content);
        return filePath;
    }

    private Guid CreateTestSession()
    {
        var session = new UserSession
        {
            SessionStartTime = DateTime.Now,
            lastUseTime = DateTime.Now
        };
        _context.UserSessions.Add(session);


       /* var userdata = new UserOBDData()
        {
            UserSessionId = session.Id,
            UploadedAt = DateTime.Now,
            Model = "focus"
        };

        _context.UserOBDDatas.Add(userdata);*/
        _context.SaveChanges();
        return session.Id;
    }

    #region ParsePercentageOrNumber Tests

    [Fact]
    public void ParsePercentageOrNumber_NumericString_ReturnsDouble()
    {
        var result = ChatController.ParsePercentageOrNumber("75.5");

        result.Should().Be(75.5);
    }

    [Fact]
    public void ParsePercentageOrNumber_PercentageString_ReturnsDouble()
    {
        var result = ChatController.ParsePercentageOrNumber("75.5%");

        result.Should().Be(75.5);
    }

    [Fact]
    public void ParsePercentageOrNumber_Null_ReturnsNull()
    {
        var result = ChatController.ParsePercentageOrNumber(null);

        result.Should().BeNull();
    }

    [Fact]
    public void ParsePercentageOrNumber_EmptyString_ReturnsNull()
    {
        var result = ChatController.ParsePercentageOrNumber("");

        result.Should().BeNull();
    }

    [Fact]
    public void ParsePercentageOrNumber_NonNumeric_ReturnsNull()
    {
        var result = ChatController.ParsePercentageOrNumber("abc");

        result.Should().BeNull();
    }

    [Fact]
    public void ParsePercentageOrNumber_WhitespaceWithPercent_ReturnsDouble()
    {
        var result = ChatController.ParsePercentageOrNumber(" 75 % ");

        result.Should().Be(75.0);
    }

    [Fact]
    public void ParsePercentageOrNumber_IntegerString_ReturnsDouble()
    {
        var result = ChatController.ParsePercentageOrNumber("100");

        result.Should().Be(100.0);
    }

    [Fact]
    public void ParsePercentageOrNumber_NegativeNumber_ReturnsNegativeDouble()
    {
        var result = ChatController.ParsePercentageOrNumber("-10.5");

        result.Should().Be(-10.5);
    }

    #endregion

    #region ExtractRelevantDataFromFile Tests

    [Fact]
    public void ExtractRelevantDataFromFile_ValidCsv_ReturnsTrue()
    {
        var sessionId = CreateTestSession();
        var csv = "MARK,MODEL,CAR_YEAR,ENGINE_POWER\nToyota,Corolla,2020,1.8";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeTrue();
        var obdData = _context.UserOBDDatas.FirstOrDefault(d => d.UserSessionId == sessionId);
        obdData.Should().NotBeNull();
        obdData!.Mark.Should().Be("Toyota");
        obdData.Model.Should().Be("Corolla");
        obdData.CarYear.Should().Be("2020");
    }

    [Fact]
    public void ExtractRelevantDataFromFile_NonexistentFile_ReturnsFalse()
    {
        var sessionId = CreateTestSession();

        var result = _controller.ExtractRelevantDataFromFile(sessionId, @"C:\nonexistent\file.csv");

        result.Should().BeFalse();
    }

    [Fact]
    public void ExtractRelevantDataFromFile_HeadersOnly_ReturnsFalse()
    {
        var sessionId = CreateTestSession();
        var csv = "MARK,MODEL,CAR_YEAR";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeFalse();
    }

    [Fact]
    public void ExtractRelevantDataFromFile_MismatchedColumns_ReturnsFalse()
    {
        var sessionId = CreateTestSession();
        var csv = "MARK,MODEL,CAR_YEAR\nToyota,Corolla";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeFalse();
    }

    [Fact]
    public void ExtractRelevantDataFromFile_UnknownHeaders_IgnoredGracefully()
    {
        var sessionId = CreateTestSession();
        var csv = "MARK,UNKNOWN_FIELD,MODEL\nToyota,SomeValue,Corolla";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeTrue();
        var obdData = _context.UserOBDDatas.FirstOrDefault(d => d.UserSessionId == sessionId);
        obdData.Should().NotBeNull();
        obdData!.Mark.Should().Be("Toyota");
        obdData.Model.Should().Be("Corolla");
    }

    [Fact]
    public void ExtractRelevantDataFromFile_AllKnownHeaders_MapsCorrectly()
    {
        var sessionId = CreateTestSession();
        var csv = "MARK,MODEL,CAR_YEAR,ENGINE_RPM,FUEL_LEVEL,TROUBLE_CODES,SPEED\n" +
                  "Ford,Focus,2015,3000,50.5,P0300,60";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeTrue();
        var obdData = _context.UserOBDDatas.FirstOrDefault(d => d.UserSessionId == sessionId);
        obdData.Should().NotBeNull();
        obdData!.Mark.Should().Be("Ford");
        obdData.EngineRpm.Should().Be("3000");
        obdData.FuelLevel.Should().Be("50.5");
        obdData.TroubleCodes.Should().Be("P0300");
        obdData.Speed.Should().Be("60");
    }

    [Fact]
    public void ExtractRelevantDataFromFile_CaseInsensitiveHeaders_MapsCorrectly()
    {
        var sessionId = CreateTestSession();
        var csv = "mark,model,car_year\ntoyota,corolla,2020";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeTrue();
        var obdData = _context.UserOBDDatas.FirstOrDefault(d => d.UserSessionId == sessionId);
        obdData.Should().NotBeNull();
        obdData!.Mark.Should().Be("toyota");
    }

    [Fact]
    public void ExtractRelevantDataFromFile_EmptyFile_ReturnsFalse()
    {
        var sessionId = CreateTestSession();
        var filePath = CreateTempCsvFile("");

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeFalse();
    }

    [Fact]
    public void ExtractRelevantDataFromFile_WithTimestamp_ParsesDateComponents()
    {
        var sessionId = CreateTestSession();

        var csv = "MARK,TIMESTAMP\nToyota,2024-05-10 14:30:00";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeTrue();

        var obdData = _context.UserOBDDatas.FirstOrDefault(d => d.UserSessionId == sessionId);

        obdData.Should().NotBeNull();
        obdData!.Hours.Should().Be("14");
        obdData.Min.Should().Be("30");
        obdData.Year.Should().Be("2024");
    }

    [Fact]
    public void ExtractRelevantDataFromFile_TimeOnly_ParsesHoursAndMinutes()
    {
        var sessionId = CreateTestSession();

        var csv = "MARK,TIME\nToyota,10:45";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeTrue();

        var obdData = _context.UserOBDDatas.FirstOrDefault(d => d.UserSessionId == sessionId);

        obdData.Should().NotBeNull();
        obdData!.Hours.Should().Be("10");
        obdData.Min.Should().Be("45");
    }

    [Fact]
    public void ExtractRelevantDataFromFile_TimestampEmpty_Ignored()
    {
        var sessionId = CreateTestSession();

        var csv = "MARK,TIMESTAMP\nToyota,";
        var filePath = CreateTempCsvFile(csv);

        var result = _controller.ExtractRelevantDataFromFile(sessionId, filePath);

        result.Should().BeTrue();

        var obdData = _context.UserOBDDatas.FirstOrDefault(d => d.UserSessionId == sessionId);

        obdData.Should().NotBeNull();
        obdData!.Hours.Should().BeNull();
    }

    #endregion

    #region T&C Tests

    [Fact]
    public void Index_ReturnsView()
    {
        var result = _controller.Index();

        result.Should().BeOfType<ViewResult>();
    }

    [Fact]
    public void TandCDisagree_ReturnsView()
    {
        var result = _controller.TandCDisagree();

        result.Should().BeOfType<ViewResult>();
    }

    [Fact]
    public async Task TandCAgree_CreatesSession_ReturnsView()
    {
        var result = await _controller.TandCAgree();

        result.Should().BeOfType<ViewResult>();

        _context.UserSessions.Count().Should().Be(1);
    }

    #endregion

    #region File Uploading Tests

    [Fact]
    public async Task UploadFile_NoSession_ReturnsBadRequest()
    {
        var fakeFile = new Mock<IFormFile>();

        var result = await _controller.UploadFile(Guid.NewGuid(), fakeFile.Object);

        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task UploadFile_EmptyFile_ReturnsViewWithMessage()
    {
        var sessionId = CreateTestSession();

        var fileMock = new Mock<IFormFile>();
        fileMock.Setup(f => f.Length).Returns(0);

        var result = await _controller.UploadFile(sessionId, fileMock.Object);

        result.Should().BeOfType<ViewResult>();
    }

    [Fact]
    public async Task UploadFile_InvalidFileType_ReturnsErrorView()
    {
        var sessionId = CreateTestSession();

        var fileMock = new Mock<IFormFile>();
        fileMock.Setup(f => f.Length).Returns(100);
        fileMock.Setup(f => f.FileName).Returns("file.txt");

        var result = await _controller.UploadFile(sessionId, fileMock.Object);

        result.Should().BeOfType<ViewResult>();
    }

    #endregion

    #region LetsChat Tests

    [Fact]
    public async Task LetsChat_InvalidSession_ReturnsBadRequest()
    {
        var result = await _controller.LetsChat(Guid.NewGuid());

        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task LetsChat_NoChats_CreatesInitialChat()
    {
        var sessionId = CreateTestSession();

        var userdata = new UserOBDData()
           {
               UserSessionId = sessionId,
               UploadedAt = DateTime.Now,
               Model = "focus"
           };

           _context.UserOBDDatas.Add(userdata);

        var result = await _controller.LetsChat(sessionId);

        result.Should().BeOfType<ViewResult>();

        _context.UserChatItems.Count().Should().Be(1);
    }

    [Fact]
    public async Task NewChatMessage_EmptyMessage_ReturnsBadRequest()
    {
        var sessionId = CreateTestSession();

        var result = await _controller.newChatMessage(sessionId, "");

        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task NewChatMessage_ValidMessage_SavesChat()
    {
        var sessionId = CreateTestSession();

        var result = await _controller.newChatMessage(sessionId, "Hello bot");

        result.Should().BeOfType<RedirectToActionResult>();

        _context.UserChatItems.Count().Should().BeGreaterThan(0);
    }

    #endregion

    #region RemoveData

    [Fact]
    public void RemoveMyData_SessionNotFound_ReturnsNotFound()
    {
        var result = _controller.RemoveMyData(Guid.NewGuid());

        result.Should().BeOfType<NotFoundObjectResult>();
    }

    [Fact]
    public void RemoveMyData_RemovesAllUserData()
    {
        var sessionId = CreateTestSession();

        _context.UserOBDDatas.Add(new UserOBDData
        {
            UserSessionId = sessionId
        });

        _context.UserChatItems.Add(new UserChatItem(
            sessionId,
            ChatSender.User,
            "test",
            0
        ));

        _context.SaveChanges();

        var result = _controller.RemoveMyData(sessionId);

        result.Should().BeOfType<ViewResult>();

        _context.UserSessions.Count().Should().Be(0);
        _context.UserOBDDatas.Count().Should().Be(0);
        _context.UserChatItems.Count().Should().Be(0);
    }

    [Fact]
    public void RemoveOldData_RemovesOldSessionsAndRelatedData()
    {
        var oldSession = new UserSession
        {
            SessionStartTime = DateTime.Now.AddHours(-1),
            lastUseTime = DateTime.Now.AddHours(-1)
        };

        _context.UserSessions.Add(oldSession);

        _context.UserOBDDatas.Add(new UserOBDData
        {
            UserSessionId = oldSession.Id
        });

        _context.UserChatItems.Add(new UserChatItem(
            oldSession.Id,
            ChatSender.User,
            "hello",
            0
        ));

        _context.SaveChanges();

        _controller.RemoveOldData();

        _context.UserSessions.Should().BeEmpty();
        _context.UserOBDDatas.Should().BeEmpty();
        _context.UserChatItems.Should().BeEmpty();
    }

    #endregion
}
