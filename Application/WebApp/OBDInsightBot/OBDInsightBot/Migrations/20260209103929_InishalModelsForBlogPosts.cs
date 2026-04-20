using Microsoft.EntityFrameworkCore.Migrations;
using System;
using System.Diagnostics.CodeAnalysis;

#nullable disable

namespace OBDInsightBot.Migrations
{
    [ExcludeFromCodeCoverage]
    /// <inheritdoc />
    public partial class InishalModelsForBlogPosts : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_UserOBDDatas_UserSessionId",
                table: "UserOBDDatas");

            migrationBuilder.RenameIndex(
                name: "IX_UserChatItems_UserSessionId",
                table: "UserChatItems",
                newName: "IX_UserChatItems_SessionId");

            migrationBuilder.CreateTable(
                name: "BlogPosts",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    WrittenAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    Title = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false),
                    MiniDescription = table.Column<string>(type: "TEXT", maxLength: 500, nullable: false),
                    Content = table.Column<string>(type: "TEXT", nullable: false),
                    PostedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    IsHidden = table.Column<bool>(type: "INTEGER", nullable: false),
                    PathForFeaturedImage = table.Column<string>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BlogPosts", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_UserSessions_LastUseTime",
                table: "UserSessions",
                column: "lastUseTime");

            migrationBuilder.CreateIndex(
                name: "IX_UserOBDData_SessionId",
                table: "UserOBDDatas",
                column: "UserSessionId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_UserChatItems_SessionId_Position",
                table: "UserChatItems",
                columns: new[] { "UserSessionId", "ChatPosition" });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "BlogPosts");

            migrationBuilder.DropIndex(
                name: "IX_UserSessions_LastUseTime",
                table: "UserSessions");

            migrationBuilder.DropIndex(
                name: "IX_UserOBDData_SessionId",
                table: "UserOBDDatas");

            migrationBuilder.DropIndex(
                name: "IX_UserChatItems_SessionId_Position",
                table: "UserChatItems");

            migrationBuilder.RenameIndex(
                name: "IX_UserChatItems_SessionId",
                table: "UserChatItems",
                newName: "IX_UserChatItems_UserSessionId");

            migrationBuilder.CreateIndex(
                name: "IX_UserOBDDatas_UserSessionId",
                table: "UserOBDDatas",
                column: "UserSessionId");
        }
    }
}
