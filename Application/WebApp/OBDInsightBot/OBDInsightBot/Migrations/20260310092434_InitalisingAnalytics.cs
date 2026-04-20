using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace OBDInsightBot.Migrations
{
    /// <inheritdoc />
    public partial class InitalisingAnalytics : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "SignleUses",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    startTime = table.Column<DateTime>(type: "TEXT", nullable: false),
                    UserChatCount = table.Column<int>(type: "INTEGER", nullable: false),
                    PreBuiltQuestions = table.Column<int>(type: "INTEGER", nullable: false),
                    ResponceErrors = table.Column<int>(type: "INTEGER", nullable: false),
                    UserSessionId = table.Column<Guid>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_SignleUses", x => x.Id);
                    table.ForeignKey(
                        name: "FK_SignleUses_UserSessions_UserSessionId",
                        column: x => x.UserSessionId,
                        principalTable: "UserSessions",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateIndex(
                name: "IX_SignleUses_UserSessionId",
                table: "SignleUses",
                column: "UserSessionId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "SignleUses");
        }
    }
}
