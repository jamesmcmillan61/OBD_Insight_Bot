using Microsoft.EntityFrameworkCore.Migrations;
using System;
using System.Diagnostics.CodeAnalysis;

#nullable disable

namespace OBDInsightBot.Migrations
{
    [ExcludeFromCodeCoverage]
    /// <inheritdoc />
    public partial class MigrationBlogpostitem : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "BlogItems",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    BlogPostId = table.Column<Guid>(type: "TEXT", nullable: false),
                    WrittenAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    type = table.Column<int>(type: "INTEGER", nullable: false),
                    contence = table.Column<string>(type: "TEXT", nullable: false),
                    cssCode = table.Column<string>(type: "TEXT", nullable: false),
                    PositionInBlog = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_BlogItems", x => x.Id);
                    table.ForeignKey(
                        name: "FK_BlogItems_BlogPosts_BlogPostId",
                        column: x => x.BlogPostId,
                        principalTable: "BlogPosts",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_BlogItems_BlogPostId",
                table: "BlogItems",
                column: "BlogPostId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "BlogItems");
        }
    }
}
