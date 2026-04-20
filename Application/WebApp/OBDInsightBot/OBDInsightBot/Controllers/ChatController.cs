using CsvHelper;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using OBDInsightBot.Models;
using OBDInsightBot.Services;
using System.Diagnostics;
using System.Globalization;
using System.Reflection;
using CsvHelper;
using System.Threading.Tasks;

namespace OBDInsightBot.Controllers
{
    public class ChatController : Controller
    {
        private readonly ApplicationDbContext _context;
        private readonly ChatbotApiService _chatbotApi;

        public ChatController(ApplicationDbContext context, ChatbotApiService chatbotApi)
        {
            _context = context;
            _chatbotApi = chatbotApi;
        }



        [HttpGet("Chat/ManualEntry")]
        public async Task<IActionResult> ManualEntry(Guid SessionID)
        {
            var selectedSession = await _context.UserSessions
                .AsNoTracking()
                .FirstOrDefaultAsync(s => s.Id == SessionID);

            if (selectedSession == null)
                return BadRequest("Invalid session.");

            ViewBag.SelectedSessionID = SessionID;

            return View();
        }

        [HttpPost]
        public async Task<IActionResult> ManualEntrySubmit(Guid SessionID, UserOBDData data)
        {
            var selectedSession = await _context.UserSessions
                .FirstOrDefaultAsync(s => s.Id == SessionID);

            if (selectedSession == null)
                return BadRequest("Invalid session.");

            // Ensure session is set correctly
            data.UserSessionId = SessionID;
            data.UploadedAt = DateTime.UtcNow;

            // Optional: Remove existing OBD data for this session
            var existing = await _context.UserOBDDatas
                .FirstOrDefaultAsync(d => d.UserSessionId == SessionID);

            if (existing != null)
            {
                _context.UserOBDDatas.Remove(existing);
            }

            _context.UserOBDDatas.Add(data);
            await _context.SaveChangesAsync();

            // Optional analytics update (same behaviour as CSV upload)
            var SU = await _context.SignleUses
                .FirstOrDefaultAsync(s => s.UserSessionId == SessionID);

            if (SU != null)
            {
                SU.UploadFileSucsessfully = true;
                _context.Update(SU);
                await _context.SaveChangesAsync();
            }

            return RedirectToAction("LetsChat", new { SessionID = SessionID });
        }



        [HttpGet("TermsOfUse")]
        public IActionResult Index()
        {
            return View();
        }

        [HttpGet("TermsOfUse/Disagreed")]
        public IActionResult TandCDisagree()
        {
            return View();
        }


        [HttpGet("TermsOfUse/Agreed")]
        public async Task<IActionResult> TandCAgree()
        {
            // Creates a new userSession and passes this into the model.
            UserSession newUserSesh = new UserSession()
            {
                SessionStartTime = DateTime.Now,
                lastUseTime = DateTime.Now,
            };
            _context.UserSessions.Add(newUserSesh);
            _context.SaveChanges();

            ViewBag.SelectedSessionID = newUserSesh.Id;


            // Creates a new Analytics profile for this session 
            SingleUse newUse = new SingleUse()
            {
                startTime = DateTime.Now,
                UserSessionId = newUserSesh.Id
            };

            _context.SignleUses.Add(newUse);
            await _context.SaveChangesAsync();


            return View(newUserSesh);
        }

        //[HttpPost]
        //public IActionResult UploadFile(Guid SessionID, File)
        //{
        //    if it fails use ViewBag.Message To send a message to the user this will be displayed. And then return a redirect to view "TandCAgree" passing in the UserSession with the Id being SessionID

        //    return RedirectToAction("LetsChat", )
        //}


        #region Upload your data
        [HttpPost]
        public async Task<IActionResult> UploadFile(Guid SessionID, IFormFile file)
        {
            UserSession selectedUS = _context.UserSessions.FirstOrDefault(US => US.Id == SessionID);
            if (selectedUS == null) return BadRequest("No session selected.");

            if (file == null || file.Length == 0)
            {
                ViewBag.Message = "Please select a CSV file to upload.";

                return View("TandCAgree", selectedUS);
            }

            try
            {

               
                // Optional: Validate file extension
                var extension = Path.GetExtension(file.FileName).ToLower();
                if (extension != ".csv")
                {
                    ViewBag.Message = "Invalid file type. Only CSV files are allowed.";
                    return View("TandCAgree", selectedUS);
                }


                var uploadFolder = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "uploads");

                if (!Directory.Exists(uploadFolder))
                {
                    Directory.CreateDirectory(uploadFolder);
                }

                // Instead of using user-supplied filename which could contain "../" sequences
                var safeFileName = $"{Guid.NewGuid()}{Path.GetExtension(file.FileName).ToLower()}";
                var filePath = Path.Combine(uploadFolder, safeFileName);

                const long maxFileSize = 10 * 1024 * 1024; // 10MB
                if (file.Length > maxFileSize)
                {
                    ViewBag.Message = "File size exceeds the maximum allowed (10MB).";
                    return View("TandCAgree", selectedUS);
                }

                using (var stream = new FileStream(filePath, FileMode.Create))
                {
                    file.CopyTo(stream);
                }

                selectedUS.UploadedDataPath = filePath;
                _context.UserSessions.Update(selectedUS);
                _context.SaveChanges();

                bool canIParse = ExtractRelevantDataFromFile(SessionID, filePath);
                if (canIParse)
                {
                    // Record anaylitics UploadFileSucsessfully as true

                    SingleUse SU = await _context.SignleUses.FirstOrDefaultAsync(S => S.UserSessionId == SessionID);
                    if (SU != null)
                    {
                        SU.UploadFileSucsessfully = true;

                        _context.Update(SU);
                        await _context.SaveChangesAsync();
                    }




                    return RedirectToAction("LetsChat", new { SessionID = SessionID });
                }
                else
                {
                    ViewBag.Message = "We were unable to extract your data. Please try again or check your data source.";
                    return View("TandCAgree", selectedUS);
                }
                    
            }
            catch (Exception ex)
            {
                // Handle any exceptions
                ViewBag.Message = "File upload failed: " + ex.Message;
                return View("TandCAgree", selectedUS);
            }
        }

        internal bool ExtractRelevantDataFromFile(Guid SessionID, string filePath)
    {
        if (!System.IO.File.Exists(filePath))
            return false;

        try
        {
                using var reader = new StreamReader(filePath);
                using var csv = new CsvReader(reader, CultureInfo.InvariantCulture);

                // Read header row
                if (!csv.Read())
                    return false;

                csv.ReadHeader();
                var headers = csv.HeaderRecord;

                // Read first data row
                if (!csv.Read())
                    return false;

                var values = new string[headers.Length];

                for (int i = 0; i < headers.Length; i++)
                {
                    values[i] = csv.GetField(i)?.Trim();
                }

                if (headers.Length != values.Length)
                    return false; // still protects your logic

                // Create the object
                var data = new UserOBDData
                {
                    UserSessionId = SessionID,
                    UploadedAt = DateTime.UtcNow
                };

                // Map CSV headers to object properties.
                // Multiple aliases per field support common OBD II tool export formats
                // (Torque Pro, OBD Auto Doctor, DashCommand, Car Scanner, etc.).
                // All lookups are case-insensitive via StringComparer.OrdinalIgnoreCase.
                var propertyMap = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
                {
                // --- Vehicle identity ---
                {"MARK",                                nameof(UserOBDData.Mark)},
                {"MAKE",                                nameof(UserOBDData.Mark)},
                {"MANUFACTURER",                        nameof(UserOBDData.Mark)},
                {"BRAND",                               nameof(UserOBDData.Mark)},
                {"VEHICLE_MAKE",                        nameof(UserOBDData.Mark)},
                {"CAR_MAKE",                            nameof(UserOBDData.Mark)},

                {"MODEL",                               nameof(UserOBDData.Model)},
                {"VEHICLE_MODEL",                       nameof(UserOBDData.Model)},
                {"CAR_MODEL",                           nameof(UserOBDData.Model)},
                {"MODEL_NAME",                          nameof(UserOBDData.Model)},

                {"CAR_YEAR",                            nameof(UserOBDData.CarYear)},
                {"VEHICLE_YEAR",                        nameof(UserOBDData.CarYear)},
                {"MODEL_YEAR",                          nameof(UserOBDData.CarYear)},
                {"MFG_YEAR",                            nameof(UserOBDData.CarYear)},
                {"MANUFACTURE_YEAR",                    nameof(UserOBDData.CarYear)},

                {"ENGINE_POWER",                        nameof(UserOBDData.EnginePower)},
                {"POWER",                               nameof(UserOBDData.EnginePower)},
                {"HORSEPOWER",                          nameof(UserOBDData.EnginePower)},
                {"HP",                                  nameof(UserOBDData.EnginePower)},
                {"KW",                                  nameof(UserOBDData.EnginePower)},
                {"ENGINE_HP",                           nameof(UserOBDData.EnginePower)},

                {"AUTOMATIC",                           nameof(UserOBDData.Automatic)},
                {"TRANSMISSION",                        nameof(UserOBDData.Automatic)},
                {"TRANS",                               nameof(UserOBDData.Automatic)},
                {"TRANS_TYPE",                          nameof(UserOBDData.Automatic)},
                {"GEARBOX",                             nameof(UserOBDData.Automatic)},
                {"GEAR_TYPE",                           nameof(UserOBDData.Automatic)},

                {"VEHICLE_ID",                          nameof(UserOBDData.VehicleId)},
                {"VIN",                                 nameof(UserOBDData.VehicleId)},
                {"VIN_NUMBER",                          nameof(UserOBDData.VehicleId)},
                {"CHASSIS_NO",                          nameof(UserOBDData.VehicleId)},
                {"CHASSIS_NUMBER",                      nameof(UserOBDData.VehicleId)},
                {"SERIAL_NO",                           nameof(UserOBDData.VehicleId)},

                // --- Pressure ---
                {"BAROMETRIC_PRESSURE(KPA)",            nameof(UserOBDData.BarometricPressureKpa)},
                {"BAROMETRIC_PRESSURE",                 nameof(UserOBDData.BarometricPressureKpa)},
                {"BARO_PRESSURE",                       nameof(UserOBDData.BarometricPressureKpa)},
                {"BARO",                                nameof(UserOBDData.BarometricPressureKpa)},
                {"BARO_PRESS",                          nameof(UserOBDData.BarometricPressureKpa)},
                {"ATMOSPHERIC_PRESSURE",                nameof(UserOBDData.BarometricPressureKpa)},

                {"INTAKE_MANIFOLD_PRESSURE",            nameof(UserOBDData.IntakeManifoldPressure)},
                {"MAP",                                 nameof(UserOBDData.IntakeManifoldPressure)},
                {"MANIFOLD_PRESSURE",                   nameof(UserOBDData.IntakeManifoldPressure)},
                {"INTAKE_PRESSURE",                     nameof(UserOBDData.IntakeManifoldPressure)},
                {"MAP_SENSOR",                          nameof(UserOBDData.IntakeManifoldPressure)},
                {"MANIFOLD_ABSOLUTE_PRESSURE",          nameof(UserOBDData.IntakeManifoldPressure)},

                {"FUEL_PRESSURE",                       nameof(UserOBDData.FuelPressure)},
                {"FP",                                  nameof(UserOBDData.FuelPressure)},
                {"FUEL_PRESS",                          nameof(UserOBDData.FuelPressure)},
                {"FUEL_RAIL_PRESSURE",                  nameof(UserOBDData.FuelPressure)},
                {"FRP",                                 nameof(UserOBDData.FuelPressure)},

                // --- Temperature ---
                {"ENGINE_COOLANT_TEMP",                 nameof(UserOBDData.EngineCoolantTemp)},
                {"COOLANT_TEMP",                        nameof(UserOBDData.EngineCoolantTemp)},
                {"ECT",                                 nameof(UserOBDData.EngineCoolantTemp)},
                {"COOLANT_TEMPERATURE",                 nameof(UserOBDData.EngineCoolantTemp)},
                {"WATER_TEMP",                          nameof(UserOBDData.EngineCoolantTemp)},
                {"ENGINE_WATER_TEMP",                   nameof(UserOBDData.EngineCoolantTemp)},
                {"COOLANT",                             nameof(UserOBDData.EngineCoolantTemp)},

                {"AMBIENT_AIR_TEMP",                    nameof(UserOBDData.AmbientAirTemp)},
                {"AMBIENT_TEMP",                        nameof(UserOBDData.AmbientAirTemp)},
                {"AMBIENT_AIR_TEMPERATURE",             nameof(UserOBDData.AmbientAirTemp)},
                {"OUTSIDE_TEMP",                        nameof(UserOBDData.AmbientAirTemp)},
                {"AAT",                                 nameof(UserOBDData.AmbientAirTemp)},
                {"EXT_TEMP",                            nameof(UserOBDData.AmbientAirTemp)},
                {"EXTERNAL_TEMP",                       nameof(UserOBDData.AmbientAirTemp)},

                {"AIR_INTAKE_TEMP",                     nameof(UserOBDData.AirIntakeTemp)},
                {"IAT",                                 nameof(UserOBDData.AirIntakeTemp)},
                {"INTAKE_AIR_TEMP",                     nameof(UserOBDData.AirIntakeTemp)},
                {"INTAKE_TEMP",                         nameof(UserOBDData.AirIntakeTemp)},
                {"AIR_INTAKE_TEMPERATURE",              nameof(UserOBDData.AirIntakeTemp)},
                {"INTAKE_AIR_TEMPERATURE",              nameof(UserOBDData.AirIntakeTemp)},

                // --- Fuel ---
                {"FUEL_LEVEL",                          nameof(UserOBDData.FuelLevel)},
                {"FUEL",                                nameof(UserOBDData.FuelLevel)},
                {"FUEL_LEVEL_INPUT",                    nameof(UserOBDData.FuelLevel)},
                {"FUEL_REMAINING",                      nameof(UserOBDData.FuelLevel)},
                {"FUEL_TANK_LEVEL",                     nameof(UserOBDData.FuelLevel)},

                {"FUEL_TYPE",                           nameof(UserOBDData.FuelType)},
                {"FUEL_SYSTEM",                         nameof(UserOBDData.FuelType)},
                {"FUEL_SYSTEM_TYPE",                    nameof(UserOBDData.FuelType)},
                {"FUEL_SYSTEM_STATUS",                  nameof(UserOBDData.FuelType)},

                {"LONG TERM FUEL TRIM BANK 2",          nameof(UserOBDData.LongTermFuelTrimBank2)},
                {"LONG_TERM_FUEL_TRIM_BANK_2",          nameof(UserOBDData.LongTermFuelTrimBank2)},
                {"LTFT_B2",                             nameof(UserOBDData.LongTermFuelTrimBank2)},
                {"LTFT2",                               nameof(UserOBDData.LongTermFuelTrimBank2)},
                {"LTFT_BANK2",                          nameof(UserOBDData.LongTermFuelTrimBank2)},
                {"LONG_TERM_FT_B2",                     nameof(UserOBDData.LongTermFuelTrimBank2)},

                {"SHORT TERM FUEL TRIM BANK 1",         nameof(UserOBDData.ShortTermFuelTrimBank1)},
                {"SHORT_TERM_FUEL_TRIM_BANK_1",         nameof(UserOBDData.ShortTermFuelTrimBank1)},
                {"STFT_B1",                             nameof(UserOBDData.ShortTermFuelTrimBank1)},
                {"STFT1",                               nameof(UserOBDData.ShortTermFuelTrimBank1)},
                {"STFT_BANK1",                          nameof(UserOBDData.ShortTermFuelTrimBank1)},
                {"SHORT_TERM_FT_B1",                    nameof(UserOBDData.ShortTermFuelTrimBank1)},

                {"SHORT TERM FUEL TRIM BANK 2",         nameof(UserOBDData.ShortTermFuelTrimBank2)},
                {"SHORT_TERM_FUEL_TRIM_BANK_2",         nameof(UserOBDData.ShortTermFuelTrimBank2)},
                {"STFT_B2",                             nameof(UserOBDData.ShortTermFuelTrimBank2)},
                {"STFT2",                               nameof(UserOBDData.ShortTermFuelTrimBank2)},
                {"STFT_BANK2",                          nameof(UserOBDData.ShortTermFuelTrimBank2)},
                {"SHORT_TERM_FT_B2",                    nameof(UserOBDData.ShortTermFuelTrimBank2)},

                {"EQUIV_RATIO",                         nameof(UserOBDData.EquivRatio)},
                {"LAMBDA",                              nameof(UserOBDData.EquivRatio)},
                {"EQUIVALENCE_RATIO",                   nameof(UserOBDData.EquivRatio)},
                {"COMMANDED_EQUIV_RATIO",               nameof(UserOBDData.EquivRatio)},
                {"AFR",                                 nameof(UserOBDData.EquivRatio)},
                {"FUEL_AIR_RATIO",                      nameof(UserOBDData.EquivRatio)},

                // --- Engine ---
                {"ENGINE_LOAD",                         nameof(UserOBDData.EngineLoad)},
                {"CALCULATED_ENGINE_LOAD",              nameof(UserOBDData.EngineLoad)},
                {"ENGINE_LOAD_VALUE",                   nameof(UserOBDData.EngineLoad)},
                {"LOAD",                                nameof(UserOBDData.EngineLoad)},
                {"CALC_ENGINE_LOAD",                    nameof(UserOBDData.EngineLoad)},
                {"ENGINE_LOAD_PCT",                     nameof(UserOBDData.EngineLoad)},

                {"ENGINE_RPM",                          nameof(UserOBDData.EngineRpm)},
                {"RPM",                                 nameof(UserOBDData.EngineRpm)},
                {"ENGINE_SPEED",                        nameof(UserOBDData.EngineRpm)},
                {"REVS",                                nameof(UserOBDData.EngineRpm)},
                {"REVOLUTIONS",                         nameof(UserOBDData.EngineRpm)},
                {"ENGINE_REVS",                         nameof(UserOBDData.EngineRpm)},

                {"ENGINE_RUNTIME",                      nameof(UserOBDData.EngineRuntime)},
                {"RUN_TIME",                            nameof(UserOBDData.EngineRuntime)},
                {"ENGINE_RUN_TIME",                     nameof(UserOBDData.EngineRuntime)},
                {"TIME_SINCE_ENGINE_START",             nameof(UserOBDData.EngineRuntime)},
                {"RUNTIME",                             nameof(UserOBDData.EngineRuntime)},
                {"ENGINE_RUN_SECS",                     nameof(UserOBDData.EngineRuntime)},

                {"MAF",                                 nameof(UserOBDData.Maf)},
                {"MAF_SENSOR",                          nameof(UserOBDData.Maf)},
                {"MASS_AIR_FLOW",                       nameof(UserOBDData.Maf)},
                {"AIR_FLOW_RATE",                       nameof(UserOBDData.Maf)},
                {"AIR_FLOW",                            nameof(UserOBDData.Maf)},
                {"MASS_AIRFLOW",                        nameof(UserOBDData.Maf)},

                {"TIMING_ADVANCE",                      nameof(UserOBDData.TimingAdvance)},
                {"IGNITION_TIMING",                     nameof(UserOBDData.TimingAdvance)},
                {"TIMING",                              nameof(UserOBDData.TimingAdvance)},
                {"TA",                                  nameof(UserOBDData.TimingAdvance)},
                {"SPARK_ADVANCE",                       nameof(UserOBDData.TimingAdvance)},

                {"THROTTLE_POS",                        nameof(UserOBDData.ThrottlePos)},
                {"THROTTLE_POSITION",                   nameof(UserOBDData.ThrottlePos)},
                {"TPS",                                 nameof(UserOBDData.ThrottlePos)},
                {"THROTTLE",                            nameof(UserOBDData.ThrottlePos)},
                {"TP",                                  nameof(UserOBDData.ThrottlePos)},
                {"THROTTLE_OPENING",                    nameof(UserOBDData.ThrottlePos)},

                // --- Speed ---
                {"SPEED",                               nameof(UserOBDData.Speed)},
                {"VEHICLE_SPEED",                       nameof(UserOBDData.Speed)},
                {"VSS",                                 nameof(UserOBDData.Speed)},
                {"GPS_SPEED",                           nameof(UserOBDData.Speed)},
                {"OBD_SPEED",                           nameof(UserOBDData.Speed)},
                {"CAR_SPEED",                           nameof(UserOBDData.Speed)},
                {"VEHICLE_SPEED_SENSOR",                nameof(UserOBDData.Speed)},

                // --- Fault codes ---
                {"DTC_NUMBER",                          nameof(UserOBDData.DtcNumber)},
                {"DTC_COUNT",                           nameof(UserOBDData.DtcNumber)},
                {"NUM_DTC",                             nameof(UserOBDData.DtcNumber)},
                {"NUMBER_OF_DTC",                       nameof(UserOBDData.DtcNumber)},
                {"FAULT_COUNT",                         nameof(UserOBDData.DtcNumber)},
                {"NUM_TROUBLE_CODES",                   nameof(UserOBDData.DtcNumber)},

                {"TROUBLE_CODES",                       nameof(UserOBDData.TroubleCodes)},
                {"DTC_CODES",                           nameof(UserOBDData.TroubleCodes)},
                {"DTC",                                 nameof(UserOBDData.TroubleCodes)},
                {"FAULT_CODES",                         nameof(UserOBDData.TroubleCodes)},
                {"ERROR_CODES",                         nameof(UserOBDData.TroubleCodes)},
                {"OBD_CODES",                           nameof(UserOBDData.TroubleCodes)},
                {"DTCS",                                nameof(UserOBDData.TroubleCodes)},
                {"P_CODES",                             nameof(UserOBDData.TroubleCodes)},

                // --- Timestamp components ---
                {"MIN",                                 nameof(UserOBDData.Min)},
                {"MINUTE",                              nameof(UserOBDData.Min)},
                {"MINUTES",                             nameof(UserOBDData.Min)},
                {"TIME_MIN",                            nameof(UserOBDData.Min)},
                {"TIME_MINUTES",                        nameof(UserOBDData.Min)},

                {"HOURS",                               nameof(UserOBDData.Hours)},
                {"HOUR",                                nameof(UserOBDData.Hours)},
                {"HR",                                  nameof(UserOBDData.Hours)},
                {"HRS",                                 nameof(UserOBDData.Hours)},
                {"TIME_HOUR",                           nameof(UserOBDData.Hours)},
                {"TIME_HOURS",                          nameof(UserOBDData.Hours)},

                {"DAYS_OF_WEEK",                        nameof(UserOBDData.DaysOfWeek)},
                {"DAY_OF_WEEK",                         nameof(UserOBDData.DaysOfWeek)},
                {"DAY",                                 nameof(UserOBDData.DaysOfWeek)},
                {"WEEKDAY",                             nameof(UserOBDData.DaysOfWeek)},
                {"DOW",                                 nameof(UserOBDData.DaysOfWeek)},

                {"MONTHS",                              nameof(UserOBDData.Months)},
                {"MONTH",                               nameof(UserOBDData.Months)},
                {"MO",                                  nameof(UserOBDData.Months)},
                {"TIME_MONTH",                          nameof(UserOBDData.Months)},

                {"YEAR",                                nameof(UserOBDData.Year)},
                {"TIME_YEAR",                           nameof(UserOBDData.Year)},
                {"LOG_YEAR",                            nameof(UserOBDData.Year)},
            };

            var type = typeof(UserOBDData);

            for (int i = 0; i < headers.Length; i++)
            {
                var header = headers[i];
                if (propertyMap.TryGetValue(header, out var propertyName))
                {
                    var prop = type.GetProperty(propertyName, BindingFlags.Public | BindingFlags.Instance);
                    if (prop != null && prop.CanWrite)
                    {
                        prop.SetValue(data, values[i]);
                    }
                }
            }

            // Special handling: parse a single TIMESTAMP/TIME/DATE column into component fields.
            // Recognised aliases for a combined datetime column — common in OBD logger exports.
            // Only fills a component if it was not already set by an explicit column above,
            // so a dedicated HOURS/MIN/etc. column always wins over a timestamp-derived value.
            var timestampAliases = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                "TIMESTAMP", "TIME", "DATETIME", "DATE_TIME", "DATE",
                "LOG_TIME",  "LOG_DATE", "LOG_DATETIME", "RECORD_TIME",
                "SAMPLE_TIME", "GPS_TIME", "GPS_DATE", "GPS_DATETIME"
            };

            for (int i = 0; i < headers.Length; i++)
            {
                if (!timestampAliases.Contains(headers[i]))
                    continue;

                var raw = values[i];
                if (string.IsNullOrWhiteSpace(raw))
                    break;

                // Handles ISO 8601, UK (dd/MM/yyyy), US (MM/dd/yyyy), date-only, etc.
                if (DateTime.TryParse(raw, out var dt))
                {
                    if (data.Hours      == null) data.Hours      = dt.Hour.ToString();
                    if (data.Min        == null) data.Min        = dt.Minute.ToString();
                    if (data.DaysOfWeek == null) data.DaysOfWeek = dt.DayOfWeek.ToString();
                    if (data.Months     == null) data.Months     = dt.Month.ToString();
                    if (data.Year       == null) data.Year       = dt.Year.ToString();
                    break;
                }

                // Fallback: time-only string e.g. "10:30" or "10:30:45"
                if (TimeSpan.TryParse(raw, out var ts))
                {
                    if (data.Hours == null) data.Hours = ts.Hours.ToString();
                    if (data.Min   == null) data.Min   = ts.Minutes.ToString();
                    break;
                }
            }

            _context.UserOBDDatas.Add(data);
                _context.SaveChanges();

            return true;
        }
        catch(Exception ex)
        {
                Debug.WriteLine("BIG ERROR HERE" + ex.ToString());
            return false;
        }
    }

        #endregion


        [HttpGet("Chat/")]
        public async Task<IActionResult> LetsChat(Guid SessionID, string? lastQuestion = null)
        {
            ViewBag.SessionID = SessionID;
            ViewBag.SelectedSessionID = SessionID;

            // This fetches session, chat items, and OBD data in a single query
            UserSession? selectedUS = await _context.UserSessions
                .AsNoTracking()
                .FirstOrDefaultAsync(US => US.Id == SessionID);

            if (selectedUS == null) return BadRequest("No session selected.");

            // Fetch chat items in a single query with ordering
            List<UserChatItem> chatlist = await _context.UserChatItems
                .Where(UC => UC.UserSessionId == SessionID)
                .OrderBy(c => c.ChatPosition)
                .AsNoTracking()
                .ToListAsync();

            if (chatlist.Count == 0)
            {
                // There isn't any chats yet so add an initial one
                UserChatItem initialChat = new UserChatItem(SessionID,
                    ChatSender.System,
                    "Welcome to your OBD ",
                    0);

                _context.UserChatItems.Add(initialChat);
                await _context.SaveChangesAsync();

                chatlist.Add(initialChat);
            }
            ViewBag.UsersChats = chatlist;

            // Fetch OBD data in a single query
            ViewBag.selectedcarOBDData = await _context.UserOBDDatas
                .AsNoTracking()
                .FirstOrDefaultAsync(D => D.UserSessionId == SessionID);



            UserOBDData? selectedOBDData = await _context.UserOBDDatas.FirstOrDefaultAsync(D => D.UserSessionId == SessionID) ?? null;

            if (selectedOBDData == null) return BadRequest("No data found");
            ViewBag.Questions = generateQuestions(lastQuestion, selectedOBDData);


            return View(selectedUS);
        }

        [HttpPost]
        public async Task<IActionResult> newChatMessage(Guid SessionID, string message, bool SuggestedPrompt = false)
        {
            ViewBag.SelectedSessionID = SessionID;

            // Input validation for message
            if (string.IsNullOrWhiteSpace(message))
            {
                return BadRequest("Message cannot be empty.");
            }

            // Limit message length to prevent abuse (max 1000 characters)
            const int maxMessageLength = 1000;
            if (message.Length > maxMessageLength)
            {
                message = message.Substring(0, maxMessageLength);
            }

            // Trim whitespace
            message = message.Trim();

            // FIX: Use async methods for better performance
            bool doesContainID = await _context.UserSessions.AnyAsync(S => S.Id == SessionID);
            if (!doesContainID) { return BadRequest("Cannot create message. Please start your conversation."); }

            int numberOfMessages = await _context.UserChatItems.CountAsync(c => c.UserSessionId == SessionID);
            UserChatItem userChat = new UserChatItem(SessionID,
                ChatSender.User,
                message, numberOfMessages
            );

            _context.UserChatItems.Add(userChat);

            // Update last activity time
            UserSession? selectedSession = await _context.UserSessions.FirstOrDefaultAsync(s => s.Id == SessionID);
            if (selectedSession != null)
            {
                selectedSession.lastUseTime = DateTime.UtcNow;
                _context.Update(selectedSession);
            }
            else
            {
                return BadRequest();
            }



            SingleUse SU = await _context.SignleUses.FirstOrDefaultAsync(S => S.UserSessionId == SessionID);
            if (SU != null)
            {
                SU.UserChatCount = SU.UserChatCount + 1;

                if(SuggestedPrompt == true)
                {
                    SU.PreBuiltQuestions = SU.PreBuiltQuestions + 1;
                }

                _context.Update(SU);
                
            }


            await _context.SaveChangesAsync();

            await ResponceFromBot(SessionID, message);

            ViewBag.selectedcarOBDData = await _context.UserOBDDatas
                .AsNoTracking()
                .FirstOrDefaultAsync(D => D.UserSessionId == SessionID);

            return RedirectToAction("LetsChat", new { SessionID = SessionID, lastQuestion = message });
        }


        // Helper method to parse values that may contain % signs
        internal static double? ParsePercentageOrNumber(string? value)
        {
            if (string.IsNullOrEmpty(value)) return null;
            // Remove % sign and whitespace
            var cleaned = value.Replace("%", "").Trim();
            return double.TryParse(cleaned, out var result) ? result : null;
        }

        public async Task<bool> ResponceFromBot(Guid SessionID, string userMessage)
        {
            try
            {
                // Get vehicle data for this session - use async
                var obdData = await _context.UserOBDDatas
                    .AsNoTracking()
                    .FirstOrDefaultAsync(d => d.UserSessionId == SessionID);

                // Convert to format expected by Python API
                var vehicleData = new
                {
                    mark = obdData?.Mark,
                    model = obdData?.Model,
                    car_year = int.TryParse(obdData?.CarYear, out var year) ? year : (int?)null,
                    engine_power = double.TryParse(obdData?.EnginePower, out var engPwr) ? engPwr : (double?)null,
                    automatic = obdData?.Automatic,
                    fuel_type = obdData?.FuelType,
                    fuel_level = ParsePercentageOrNumber(obdData?.FuelLevel),
                    engine_coolant_temp = ParsePercentageOrNumber(obdData?.EngineCoolantTemp),
                    engine_rpm = int.TryParse(obdData?.EngineRpm, out var rpm) ? rpm : (int?)null,
                    speed = int.TryParse(obdData?.Speed, out var spd) ? spd : (int?)null,
                    trouble_codes = obdData?.TroubleCodes?.Split(',', StringSplitOptions.RemoveEmptyEntries).ToList(),
                    // Additional fields for complete data transfer
                    engine_runtime = obdData?.EngineRuntime,
                    engine_load = ParsePercentageOrNumber(obdData?.EngineLoad),
                    fuel_pressure = ParsePercentageOrNumber(obdData?.FuelPressure),
                    ambient_air_temp = ParsePercentageOrNumber(obdData?.AmbientAirTemp),
                    air_intake_temp = ParsePercentageOrNumber(obdData?.AirIntakeTemp),
                    throttle_pos = ParsePercentageOrNumber(obdData?.ThrottlePos)
                };

                // Call the Python API
                string botResponse = await _chatbotApi.GetBotResponseAsync(
                    userMessage,
                    SessionID.ToString(),
                    vehicleData
                );

                // Save bot response to database - use async
                int messageCount = await _context.UserChatItems.CountAsync(c => c.UserSessionId == SessionID);
                var botChat = new UserChatItem(SessionID, ChatSender.Bot, botResponse, messageCount);
                _context.UserChatItems.Add(botChat);
                await _context.SaveChangesAsync();

                if(botResponse.Contains("Please try again later"))
                {
                    // Bot failed to connect 
                    SingleUse? SU = await _context.SignleUses.FirstOrDefaultAsync(S => S.UserSessionId == SessionID) ?? null;
                    if (SU != null)
                    {
                        Debug.WriteLine($"{SU.UserSessionId} Increasing error");
                        SU.ResponceErrors = SU.ResponceErrors + 1;

                        _context.Update(SU);

                    }


                    await _context.SaveChangesAsync();
                }

                // Adds random delay to the responce time. 
                Random rnd = new Random();
                int delay = rnd.Next(1000, 5000);
                await Task.Delay(delay);
                return true;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error getting bot response: {ex.Message}");

                // Fallback message on error - use async
                int messageCount = await _context.UserChatItems.CountAsync(c => c.UserSessionId == SessionID);
                var errorChat = new UserChatItem(SessionID, ChatSender.Bot,
                    "Sorry, I'm having trouble connecting to the chatbot service. Please try again.", messageCount);
                _context.UserChatItems.Add(errorChat);


                SingleUse? SU = await _context.SignleUses.FirstOrDefaultAsync(S => S.UserSessionId == SessionID) ?? null;
                if (SU != null)
                {
                    Debug.WriteLine($"{SU.UserSessionId} Increasing error");
                    SU.ResponceErrors = SU.ResponceErrors + 1;

                    _context.Update(SU);

                }


                await _context.SaveChangesAsync();
                return false;
            }
        }



        public IActionResult RemoveMyData(Guid SessionID)
        {
            // Fetch objects
            var selectedUS = _context.UserSessions
                .FirstOrDefault(s => s.Id == SessionID);

            var selectedData = _context.UserOBDDatas
                .FirstOrDefault(s => s.UserSessionId == SessionID);

            var selectedChats = _context.UserChatItems
                .Where(s => s.UserSessionId == SessionID)
                .ToList();

            // Safety checks
            if (selectedUS == null)
            {
                // session doesn't exist
                return NotFound("User session not found.");
            }

            // Delete related chats
            if (selectedChats.Any())
                _context.UserChatItems.RemoveRange(selectedChats);

            // Delete OBD data if exists
            if (selectedData != null)
                _context.UserOBDDatas.Remove(selectedData);

            // Get file path BEFORE removing the session from the DB
            var filePath = selectedUS.UploadedDataPath;



            // remove their anaylitic link
            SingleUse? SU = _context.SignleUses.FirstOrDefault(S => S.UserSessionId == SessionID) ?? null;
            if (SU != null)
            {
                SU.UserSession = null;
                SU.UserSessionId = null;

                _context.Update(SU);

            }



            // Delete session record
            _context.UserSessions.Remove(selectedUS);

            _context.SaveChanges();

            // Delete actual file if it exists
            if (!string.IsNullOrEmpty(filePath) && System.IO.File.Exists(filePath))
            {
                try
                {
                    System.IO.File.Delete(filePath);
                }
                catch (Exception ex)
                {
                    // Optional: log the error
                    Console.WriteLine($"File delete error: {ex.Message}");
                }
            }

            // Return a view or redirect
            return View();   // or RedirectToAction("Index");
        }




        internal void RemoveOldData()
        {
            List<UserSession> oldUS = _context.UserSessions.Where(us => us.lastUseTime < (DateTime.Now).AddMinutes(-30)).ToList();

            foreach (UserSession us in oldUS)
            {
                // gets its data and its chat history 
                UserOBDData UOBDD = _context.UserOBDDatas.FirstOrDefault(D => D.UserSessionId == us.Id) ?? null;
                if (UOBDD != null) { _context.UserOBDDatas.Remove(UOBDD); }



                var selectedChats = _context.UserChatItems
                .Where(s => s.UserSessionId == us.Id)
                .ToList();

                // Delete related chats
                if (selectedChats.Any())
                    _context.UserChatItems.RemoveRange(selectedChats);

                var filePath = us.UploadedDataPath;


                // Delete actual file if it exists
                if (!string.IsNullOrEmpty(filePath) && System.IO.File.Exists(filePath))
                {
                    try
                    {
                        System.IO.File.Delete(filePath);
                    }
                    catch (Exception ex)
                    {
                        // Optional: log the error
                        Console.WriteLine($"File delete error: {ex.Message}");
                    }
                }
            }




            _context.UserSessions.RemoveRange(oldUS);
            _context.SaveChanges();
        }


        private List<string> generateQuestions(string? previousQuestion, UserOBDData data)
        {
            var questions = new List<string>();

            // Keyword-based follow-ups
            var keywordMap = new Dictionary<string, List<string>>
            {
                ["fuel"] = new List<string>
        {
            "What is my current fuel level?",
            "Has my fuel consumption been unusual?",
            "Do I have any fuel system error codes?"
        },
                ["temperature"] = new List<string>
        {
            "Is my engine coolant temperature within normal range?",
            "Is the air intake temperature too high?",
            "Have I been overheating recently?"
        },
                ["rpm"] = new List<string>
        {
            "Does the engine RPM fluctuate?",
            "Is the idle RPM stable?",
            "Do you want a graph of RPM over time?"
        },
                ["speed"] = new List<string>
        {
            "What is my average speed?",
            "Have I had any speed-related warnings?",
            "Do you want to compare current speed to typical values?"
        },
                ["engine"] = new List<string>
        {
            "Are there any engine-related trouble codes?",
            "How is my engine load right now?",
            "Would you like an analysis of engine performance?"
        }
            };

            // Data-field-based questions
            var dataDrivenQuestions = new Dictionary<string, Func<UserOBDData, string>>
            {
                ["FuelLevel"] = d => $"Your fuel level is {d.FuelLevel}. Would you like to know your estimated range?",
                ["EngineCoolantTemp"] = d => $"Engine coolant temperature is {d.EngineCoolantTemp}. Want to check if this is normal?",
                ["EngineRpm"] = d => $"Your RPM is {d.EngineRpm}. Do you want a breakdown of RPM usage?",
                ["Speed"] = d => $"You're currently traveling at {d.Speed}. Want more driving insights?",
                ["TroubleCodes"] = d => $"I detected trouble codes ({d.TroubleCodes}). Want an explanation?",
            };

            // FIRST QUESTION EVER?
            if (string.IsNullOrWhiteSpace(previousQuestion))
            {
                var defaults = new List<string>
        {
            "Are there any error codes?",
            "What is my fuel level?",
            "How is my engine running?"
        };
                return defaults;
            }

            // Match keywords in previousQuestion
            foreach (var kvp in keywordMap)
            {
                if (previousQuestion.Contains(kvp.Key, StringComparison.OrdinalIgnoreCase))
                {
                    UpdateTopic(kvp.Key.ToString());
                    questions.AddRange(kvp.Value);
                }
            }

            // Generate contextual questions based on available data
            foreach (var field in dataDrivenQuestions)
            {
                var property = typeof(UserOBDData).GetProperty(field.Key);
                var value = property?.GetValue(data)?.ToString();

                if (!string.IsNullOrWhiteSpace(value))
                {
                    questions.Add(field.Value(data));
                }
            }

            return questions.Distinct().Take(3).ToList(); 
        }


        private async Task UpdateTopic(string topicName)
        {
            // Convert the incoming string to enum safely
            if (!Enum.TryParse<TopicAnalytic.TopicType>(topicName, true, out var topicEnum))
            {
                throw new ArgumentException($"Invalid topic name: {topicName}");
            }

            var today = DateOnly.FromDateTime(DateTime.Now);

            // Try to find an existing topic for today
            var existing = await _context.TopicAnalytics
                .FirstOrDefaultAsync(t => t.Date == today && t.TopicName == topicEnum);

            if (existing != null)
            {
                existing.TopicCount++;
                await _context.SaveChangesAsync();
                return;
            }

            // Create a new analytics record
            var newTopic = new TopicAnalytic
            {
                Date = today,
                TopicCount = 1,
                TopicName = topicEnum
            };

            _context.TopicAnalytics.Add(newTopic);
            await _context.SaveChangesAsync();
        }


        public async Task<IActionResult> MyCarData(Guid? SessionID)
        {
            if (SessionID == Guid.Empty || SessionID == null)
            {
                return RedirectToAction("Index");
            }

            // gets the data for this sesssion
            ViewBag.selectedSessionID = SessionID;

            UserOBDData? selecteddata = await _context.UserOBDDatas.FirstOrDefaultAsync(D => D.UserSessionId == SessionID) ?? null;
            if (selecteddata == null) { return RedirectToAction("Index"); }
            ViewBag.selectedcarOBDData = selecteddata;
            return View(selecteddata);
        }
    }
}
