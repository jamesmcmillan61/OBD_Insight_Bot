using Microsoft.EntityFrameworkCore.Migrations;
using System;
using System.Diagnostics.CodeAnalysis;

#nullable disable

namespace OBDInsightBot.Migrations
{
    [ExcludeFromCodeCoverage]
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "UserSessions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    SessionStartTime = table.Column<DateTime>(type: "TEXT", nullable: false),
                    lastUseTime = table.Column<DateTime>(type: "TEXT", nullable: false),
                    UploadedDataPath = table.Column<string>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserSessions", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "UserChatItems",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    UserSessionId = table.Column<Guid>(type: "TEXT", nullable: false),
                    ItemBy = table.Column<int>(type: "INTEGER", nullable: false),
                    ChatPosition = table.Column<int>(type: "INTEGER", nullable: false),
                    SentAtUtc = table.Column<DateTime>(type: "TEXT", nullable: false),
                    ChatContent = table.Column<string>(type: "TEXT", maxLength: 4000, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserChatItems", x => x.Id);
                    table.ForeignKey(
                        name: "FK_UserChatItems_UserSessions_UserSessionId",
                        column: x => x.UserSessionId,
                        principalTable: "UserSessions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "UserOBDDatas",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    UserSessionId = table.Column<Guid>(type: "TEXT", nullable: false),
                    UploadedAt = table.Column<DateTime>(type: "TEXT", nullable: false),
                    Mark = table.Column<string>(type: "TEXT", nullable: true),
                    Model = table.Column<string>(type: "TEXT", nullable: true),
                    CarYear = table.Column<string>(type: "TEXT", nullable: true),
                    EnginePower = table.Column<string>(type: "TEXT", nullable: true),
                    Automatic = table.Column<string>(type: "TEXT", nullable: true),
                    VehicleId = table.Column<string>(type: "TEXT", nullable: true),
                    BarometricPressureKpa = table.Column<string>(type: "TEXT", nullable: true),
                    EngineCoolantTemp = table.Column<string>(type: "TEXT", nullable: true),
                    FuelLevel = table.Column<string>(type: "TEXT", nullable: true),
                    EngineLoad = table.Column<string>(type: "TEXT", nullable: true),
                    AmbientAirTemp = table.Column<string>(type: "TEXT", nullable: true),
                    EngineRpm = table.Column<string>(type: "TEXT", nullable: true),
                    IntakeManifoldPressure = table.Column<string>(type: "TEXT", nullable: true),
                    Maf = table.Column<string>(type: "TEXT", nullable: true),
                    LongTermFuelTrimBank2 = table.Column<string>(type: "TEXT", nullable: true),
                    ShortTermFuelTrimBank1 = table.Column<string>(type: "TEXT", nullable: true),
                    ShortTermFuelTrimBank2 = table.Column<string>(type: "TEXT", nullable: true),
                    FuelType = table.Column<string>(type: "TEXT", nullable: true),
                    AirIntakeTemp = table.Column<string>(type: "TEXT", nullable: true),
                    FuelPressure = table.Column<string>(type: "TEXT", nullable: true),
                    Speed = table.Column<string>(type: "TEXT", nullable: true),
                    EngineRuntime = table.Column<string>(type: "TEXT", nullable: true),
                    ThrottlePos = table.Column<string>(type: "TEXT", nullable: true),
                    DtcNumber = table.Column<string>(type: "TEXT", nullable: true),
                    TroubleCodes = table.Column<string>(type: "TEXT", nullable: true),
                    TimingAdvance = table.Column<string>(type: "TEXT", nullable: true),
                    EquivRatio = table.Column<string>(type: "TEXT", nullable: true),
                    Min = table.Column<string>(type: "TEXT", nullable: true),
                    Hours = table.Column<string>(type: "TEXT", nullable: true),
                    DaysOfWeek = table.Column<string>(type: "TEXT", nullable: true),
                    Months = table.Column<string>(type: "TEXT", nullable: true),
                    Year = table.Column<string>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserOBDDatas", x => x.Id);
                    table.ForeignKey(
                        name: "FK_UserOBDDatas_UserSessions_UserSessionId",
                        column: x => x.UserSessionId,
                        principalTable: "UserSessions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_UserChatItems_UserSessionId",
                table: "UserChatItems",
                column: "UserSessionId");

            migrationBuilder.CreateIndex(
                name: "IX_UserOBDDatas_UserSessionId",
                table: "UserOBDDatas",
                column: "UserSessionId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "UserChatItems");

            migrationBuilder.DropTable(
                name: "UserOBDDatas");

            migrationBuilder.DropTable(
                name: "UserSessions");
        }
    }
}
