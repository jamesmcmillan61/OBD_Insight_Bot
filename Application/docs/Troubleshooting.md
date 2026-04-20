# Troubleshooting

This guide helps resolve common issues encountered during project setup and will be expanded as implementation progresses.

**Status**: Planning Phase - Most troubleshooting sections are for future reference once implementation begins

## Table of Contents

- [Development Environment Setup](#current-phase-development-environment-setup)
- [Build and Compilation](#future-reference-build-and-compilation)
- [Database Issues](#future-reference-database-issues)
- [IBM Granite AI Integration](#future-reference-ibm-granite-ai-integration)
- [Runtime and Deployment](#future-reference-runtime-and-deployment)

---

## Development Environment Setup

These are issues you may encounter NOW during project setup.

---

### Development Environment Issues

### Issue: .NET SDK Not Found

**Symptom**: Command `dotnet --version` returns "command not found"

**Cause**: .NET SDK not installed or not in PATH

**Solution**:
1. Download and install .NET 8.0 SDK from [Microsoft](https://dotnet.microsoft.com/download/dotnet/8.0)
2. After installation, restart terminal/command prompt
3. Verify installation:
   ```bash
   dotnet --version
   ```
4. If still not found, add to PATH manually:
   - **Windows**: Add `C:\Program Files\dotnet` to PATH environment variable
   - **Mac/Linux**: Add `/usr/local/share/dotnet` to PATH in `.bashrc` or `.zshrc`

---

### Issue: Visual Studio Can't Find Solution File

**Symptom**: Error opening project in Visual Studio

**Cause**: Solution file (.sln) not created yet

**Solution**:
```bash
# Create solution file
dotnet new sln --name IBMOBDInsightBot

# Add projects to solution (once created)
dotnet sln add API/API.csproj
dotnet sln add WebApp/WebApp.csproj
dotnet sln add Tests/Tests.csproj
```

---

### Issue: NuGet Package Restore Failures

**Symptom**: Error restoring NuGet packages, build fails

**Possible Causes**:
- No internet connection
- Corporate proxy blocking requests
- Corrupted NuGet cache

**Solutions**:

1. **Clear NuGet cache**:
   ```bash
   dotnet nuget locals all --clear
   dotnet restore
   ```

2. **Check NuGet sources**:
   ```bash
   dotnet nuget list source
   ```

3. **Add NuGet.org source if missing**:
   ```bash
   dotnet nuget add source https://api.nuget.org/v3/index.json --name nuget.org
   ```

4. **Configure proxy** (if behind corporate firewall):
   ```bash
   # Set environment variables
   set HTTP_PROXY=http://proxy.company.com:8080
   set HTTPS_PROXY=http://proxy.company.com:8080
   ```

---

## Build and Compilation

### Build Errors

#### Issue: CS0246 - Type or Namespace Not Found

**Symptom**: `The type or namespace name 'X' could not be found`

**Cause**: Missing using statement or NuGet package not restored

**Solution** (when applicable):
1. Add missing using statement: `using Microsoft.EntityFrameworkCore;`
2. Restore packages: `dotnet restore`
3. Check if package is referenced in `.csproj` file
4. Rebuild solution: `dotnet build`

---

### Issue: Build Succeeds But Tests Fail

**Symptom**: `dotnet build` succeeds, but `dotnet test` fails

**Common Causes**:
- Missing test dependencies
- Test database not configured
- Environment variables not set

**Solution**:
1. Check test project has all required packages:
   ```xml
   <PackageReference Include="xunit" Version="2.4.2" />
   <PackageReference Include="Moq" Version="4.18.4" />
   ```

2. Restore test project packages:
   ```bash
   dotnet restore Tests/Tests.csproj
   dotnet build Tests/Tests.csproj
   dotnet test Tests/Tests.csproj
   ```

---

## Reference: Database Issues

### Issue: LocalDB Connection Failed

**Symptom**: `Cannot connect to (localdb)\mssqllocaldb`

**Cause**: LocalDB not installed or not running

**Solution**:

1. **Check if LocalDB is installed**:
   ```bash
   sqllocaldb info
   ```

2. **Install LocalDB** (if not installed):
   - Download SQL Server Express with LocalDB from [Microsoft](https://www.microsoft.com/en-us/sql-server/sql-server-downloads)

3. **Create and start LocalDB instance**:
   ```bash
   sqllocaldb create MSSQLLocalDB
   sqllocaldb start MSSQLLocalDB
   sqllocaldb info MSSQLLocalDB
   ```

4. **Update connection string** in `appsettings.Development.json`:
   ```json
   {
     "ConnectionStrings": {
       "DefaultConnection": "Server=(localdb)\\MSSQLLocalDB;Database=OBDInsightBot;Trusted_Connection=true;"
     }
   }
   ```

---

### Issue: Entity Framework Migration Fails

**Symptom**: `dotnet ef database update` fails

**Common Causes**:
- EF tools not installed
- Invalid connection string
- SQL Server not running

**Solutions**:

1. **Install EF Core tools**:
   ```bash
   dotnet tool install --global dotnet-ef
   dotnet tool update --global dotnet-ef
   ```

2. **Verify connection string**:
   - Check `appsettings.Development.json`
   - Test connection using SQL Server Management Studio or Azure Data Studio

3. **Generate migration** (if first time):
   ```bash
   dotnet ef migrations add InitialCreate --project API
   ```

4. **Apply migration**:
   ```bash
   dotnet ef database update --project API
   ```

5. **Check migration history**:
   ```sql
   SELECT * FROM __EFMigrationsHistory;
   ```

---

### Issue: Database Locked Error

**Symptom**: `Database is locked` or `timeout expired`

**Cause**: Another process has exclusive lock on database

**Solution**:
1. Close all applications connected to database
2. Restart LocalDB:
   ```bash
   sqllocaldb stop MSSQLLocalDB
   sqllocaldb start MSSQLLocalDB
   ```
3. If persists, delete and recreate database:
   ```bash
   dotnet ef database drop --project API
   dotnet ef database update --project API
   ```

---

## IBM Granite AI Integration

### Model Connection Issues

The VM is hosted on windows platform, potential issues may include:
- Connection failures to hosted model
- Authentication/authorization issues
- Model loading errors
- Resource constraints (memory, no GPU)

**Solution**:
- Ask IT for more Resources
- Ask IT to re establish connections
- Follow deployment guide
---

### Issue: IBM Granite API Timeout

**Symptom**: Requests to Granite API timeout after 5 seconds

**Causes**:
- Network connectivity issues
- API overloaded
- Request too complex

**Solutions**:

1. **Check internet connectivity**:
   ```bash
   ping us-south.ml.cloud.ibm.com
   ```

2. **Increase timeout**:
   ```csharp
   _httpClient.Timeout = TimeSpan.FromSeconds(10);
   ```

3. **Simplify request**:
   - Reduce conversation history sent
   - Lower `max_new_tokens` parameter
   - Remove unnecessary function definitions

4. **Implement retry logic**:
   ```csharp
   int retries = 3;
   for (int i = 0; i < retries; i++)
   {
       try
       {
           return await CallGraniteAPI(request);
       }
       catch (TaskCanceledException) when (i < retries - 1)
       {
           await Task.Delay(1000 * (i + 1));
       }
   }
   ```

---

### Issue: IBM Granite Returns Empty or Invalid Response

**Symptom**: Response is empty or doesn't make sense

**Causes**:
- Model parameters not optimal
- Prompt not clear
- Function calling misconfigured

**Solutions**:

1. **Check response parsing**:
   ```csharp
   var response = await httpResponse.Content.ReadAsStringAsync();
   _logger.LogInformation("Raw response: {Response}", response);
   ```

2. **Adjust model parameters**:
   ```csharp
   parameters = new
   {
       max_new_tokens = 500,  // Increase if responses truncated
       temperature = 0.7f,    // Lower for more deterministic
       top_p = 0.9f
   }
   ```

3. **Improve prompt clarity**:
   - Add more context
   - Be specific in instructions
   - Include examples

---

### Issue: Rate Limiting Error (429)

**Symptom**: `429 Too Many Requests` from IBM Granite API

**Cause**: Exceeded API rate limits

**Solution**:

1. **Implement exponential backoff**:
   ```csharp
   if (response.StatusCode == HttpStatusCode.TooManyRequests)
   {
       var retryAfter = response.Headers.RetryAfter?.Delta ?? TimeSpan.FromSeconds(5);
       await Task.Delay(retryAfter);
       // Retry request
   }
   ```

2. **Cache responses** (future enhancement):
   - Cache common DTC explanations
   - Reduce redundant API calls

3. **Upgrade plan**: Contact IBM for higher rate limits

---

## OBD-II Data Processing

### Issue: File Upload Fails

**Symptom**: File upload returns error or hangs

**Causes**:
- File size exceeds 5MB limit (per FR-05)
- Unsupported file format
- Corrupted file

**Solutions**:

1. **Check file size**:
   ```csharp
   if (file.Length > 5 * 1024 * 1024)
   {
       return BadRequest("File size exceeds 5MB limit");
   }
   ```

2. **Validate file format**:
   ```csharp
   var allowedExtensions = new[] { ".csv", ".json" };
   var extension = Path.GetExtension(file.FileName).ToLowerInvariant();
   if (!allowedExtensions.Contains(extension))
   {
       return BadRequest("Only CSV and JSON files are supported");
   }
   ```

3. **Test with sample file**:
   - Create minimal CSV file:
     ```csv
     DTC_Code,Description
     P0301,Cylinder 1 Misfire Detected
     ```
   - Upload and verify parsing succeeds

---

### Issue: OBD-II Parsing Error

**Symptom**: Uploaded file fails to parse, error message unclear

**Causes**:
- Malformed CSV/JSON
- Unexpected file structure
- Missing required fields

**Solutions**:

1. **Log parsing details**:
   ```csharp
   try
   {
       var data = ParseOBDFile(content);
   }
   catch (Exception ex)
   {
       _logger.LogError(ex, "Parsing failed for file: {FileName}", fileName);
       throw new ParsingException($"Failed to parse file: {ex.Message}");
   }
   ```

2. **Validate file structure**:
   - Check CSV has headers
   - Verify JSON has expected schema
   - Ensure no special characters causing issues

3. **Provide helpful error messages**:
   ```csharp
   if (string.IsNullOrWhiteSpace(fileContent))
   {
       return "File is empty. Please upload a valid OBD-II diagnostic log.";
   }
   ```

---

### Issue: Invalid DTC Codes

**Symptom**: DTC codes not recognized or lookup fails

**Causes**:
- Manufacturer-specific codes (per FR-02.8)
- Typos in DTC database
- Code format invalid

**Solutions**:

1. **Validate DTC format**:
   ```csharp
   // Valid DTC format: P0301, P0420, C0035, etc.
   var dtcPattern = @"^[PCBU][0-3][0-9A-F]{3}$";
   if (!Regex.IsMatch(code, dtcPattern))
   {
       return "Invalid DTC code format";
   }
   ```

2. **Handle unknown codes gracefully** (per FR-02.8):
   ```csharp
   if (dtc == null)
   {
       return "This appears to be a manufacturer-specific code. " +
              "Please consult your vehicle's service manual for details.";
   }
   ```

3. **Log unrecognized codes**:
   ```csharp
   _logger.LogWarning("Unrecognized DTC code: {Code}", code);
   ```

---

## Runtime and Deployment

### Issue: NullReferenceException

**Symptom**: `System.NullReferenceException: Object reference not set to an instance of an object`

**Common Causes**:
- Not checking for null before accessing properties
- Dependency injection not configured
- Database query returns no results

**Solutions**:

1. **Use null-conditional operators**:
   ```csharp
   // Instead of: session.VehicleData.DTCCodes
   var dtcCodes = session?.VehicleData?.DTCCodes ?? new List<string>();
   ```

2. **Check DI configuration**:
   ```csharp
   // Ensure services are registered
   builder.Services.AddScoped<IGraniteAIService, GraniteAIService>();
   builder.Services.AddScoped<IDiagnosticService, DiagnosticService>();
   ```

3. **Validate database results**:
   ```csharp
   var session = await _context.Sessions.FindAsync(sessionId);
   if (session == null)
   {
       return NotFound($"Session {sessionId} not found");
   }
   ```

---

### Issue: SignalR Connection Failure

**Symptom**: Real-time chat not working, SignalR connection fails

**Causes**:
- CORS not configured
- Hub not mapped
- WebSocket support disabled

**Solutions**:

1. **Configure CORS for SignalR**:
   ```csharp
   builder.Services.AddCors(options =>
   {
       options.AddPolicy("SignalRPolicy", policy =>
       {
           policy.WithOrigins("https://localhost:7002")
                 .AllowAnyHeader()
                 .AllowAnyMethod()
                 .AllowCredentials();
       });
   });
   ```

2. **Map SignalR hub**:
   ```csharp
   app.MapHub<ChatHub>("/chathub");
   ```

3. **Check browser console** for connection errors

4. **Verify WebSocket support**:
   - Check browser DevTools > Network > WS tab
   - Ensure server allows WebSocket connections

---

### Issue: CORS Error in Browser

**Symptom**: Browser console shows `CORS policy: No 'Access-Control-Allow-Origin' header`

**Cause**: Backend not configured to allow frontend origin

**Solution**:

1. **Configure CORS in backend**:
   ```csharp
   builder.Services.AddCors(options =>
   {
       options.AddPolicy("AllowBlazor", policy =>
       {
           policy.WithOrigins("https://localhost:7002")
                 .AllowAnyHeader()
                 .AllowAnyMethod();
       });
   });

   app.UseCors("AllowBlazor");
   ```

2. **Verify origin matches exactly**:
   - Check frontend URL (https vs http, port number)
   - No trailing slash in origin

3. **Test with browser DevTools**:
   - Network tab > Check request headers
   - Verify `Access-Control-Allow-Origin` in response

### Performance Issues

### Issue: Slow Response Times (> 3 seconds)

**Symptom**: AI queries taking longer than 3 second target (RNF-01)

**Causes**:
- IBM Granite API latency
- Large conversation history
- Inefficient database queries

**Solutions**:

1. **Optimize conversation history**:
   ```csharp
   // Limit to last 10 exchanges (20 messages)
   var recentHistory = conversationHistory.TakeLast(20).ToList();
   ```

2. **Add performance logging**:
   ```csharp
   var stopwatch = Stopwatch.StartNew();
   var response = await _graniteService.GetResponseAsync(query);
   stopwatch.Stop();
   _logger.LogWarning("Response time: {ElapsedMs}ms", stopwatch.ElapsedMilliseconds);
   ```

3. **Use async/await properly**:
   ```csharp
   // Good - truly async
   var response = await _httpClient.GetAsync(url);

   // Bad - blocking
   var response = _httpClient.GetAsync(url).Result;
   ```

4. **Enable connection pooling**:
   ```csharp
   services.AddHttpClient<IGraniteAIService, GraniteAIService>()
       .SetHandlerLifetime(TimeSpan.FromMinutes(5));
   ```

---

### Issue: High Memory Usage

**Symptom**: Application consuming excessive memory

**Causes**:
- Memory leaks
- Large conversation history not cleaned up
- Cached data not released

**Solutions**:

1. **Implement session cleanup**:
   ```csharp
   // Clear expired sessions periodically
   public async Task CleanupExpiredSessions()
   {
       var expired = await _context.Sessions
           .Where(s => s.ExpiresAt < DateTime.UtcNow)
           .ToListAsync();

       _context.Sessions.RemoveRange(expired);
       await _context.SaveChangesAsync();
   }
   ```

2. **Dispose HttpClient properly**:
   - Use `IHttpClientFactory` instead of creating HttpClient instances

3. **Profile memory usage**:
   - Use dotMemory or Visual Studio Diagnostic Tools
   - Identify memory leaks

---

### Browser Compatibility Issues

### Issue: Application Not Working in Safari

**Symptom**: Features work in Chrome but not Safari

**Common Causes** (per RNF-07):
- WebAssembly compatibility
- CSS/JavaScript differences
- LocalStorage issues

**Solutions**:

1. **Check Safari version**: Support latest 2 versions only
2. **Test WebAssembly support**:
   ```javascript
   if (typeof WebAssembly === "undefined") {
       alert("WebAssembly not supported. Please update your browser.");
   }
   ```

3. **Check browser console** for JavaScript errors
4. **Test CSS compatibility**: Use vendor prefixes if needed

---

### Issue: File Upload Not Working on Mobile

**Symptom**: File upload button not responding on mobile browsers

**Cause**: Different file input handling on mobile

**Solution**:

1. **Ensure mobile-friendly file input**:
   ```html
   <input type="file" accept=".csv,.json" capture="environment" />
   ```

2. **Test on actual devices**: Emulators may not reflect real behavior

3. **Provide alternative** upload method (future): URL upload or cloud storage

---

### Deployment Issues

### Issue: Application Not Starting in Azure

**Symptom**: Azure App Service shows "Application Error"

**Causes**:
- Missing configuration
- Database connection failure
- Startup exception

**Solutions**:

1. **Check Application Insights logs**:
   - Azure Portal > App Service > Monitoring > Log stream

2. **Verify configuration**:
   - Check App Settings include all required values
   - Verify connection strings

3. **Test locally with production settings**:
   ```bash
   dotnet run --environment Production
   ```

4. **Enable detailed errors** (temporarily):
   ```csharp
   app.UseDeveloperExceptionPage();
   ```

---

### Issue: Database Migration Fails in Production

**Symptom**: `dotnet ef database update` fails on Azure SQL

**Causes**:
- Firewall blocking connection
- Invalid credentials
- Migration conflict

**Solutions**:

1. **Add client IP to firewall**:
   - Azure Portal > SQL Database > Firewalls and virtual networks
   - Add your IP address

2. **Test connection**:
   ```bash
   sqlcmd -S tcp:[server].database.windows.net,1433 -d [database] -U [username] -P [password]
   ```

3. **Apply migration manually**:
   ```bash
   dotnet ef database update --connection "[Azure connection string]"
   ```

---

## Getting Help

If issues persist after trying these solutions:

1. **Check Documentation**:
   - [Getting Started](./Getting-Started.md)
   - [Development Guide](./Development.md)
   - [System Architecture](./System-Architecture.md)

2. **Search Azure DevOps**:
   - Check existing work items for similar issues
   - Review closed bugs for solutions

3. **Contact Team**:
   - James McMillan: J.MCMILLAN-2021@hull.ac.uk
   - Oliver Mitchell-Paterson: O.MITCHELL-PATERSON-2021@hull.ac.uk
   - Kieran McEvoy: K.MCEVOY-2022@hull.ac.uk
   - Acker Saldana: A.SALDANA-POLANCO-2024@hull.ac.uk

4. **External Resources**:
   - [.NET Documentation](https://learn.microsoft.com/en-us/dotnet/)
   - [Blazor Documentation](https://learn.microsoft.com/en-us/aspnet/core/blazor/)
   - [IBM watsonx.ai Support](https://www.ibm.com/support)
   - [Stack Overflow](https://stackoverflow.com/) (tag: blazor, asp.net-core, entity-framework-core)

---

**Last Updated**: April 2026
**Maintained By**: IBM OBD InsightBot Team
