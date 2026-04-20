using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace OBDInsightBot.Migrations
{
    /// <inheritdoc />
    public partial class addingTopicsToUseCaseMateicsForTopic : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "TopicAnalytics",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    Date = table.Column<DateOnly>(type: "TEXT", nullable: false),
                    TopicName = table.Column<int>(type: "INTEGER", nullable: false),
                    TopicCount = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TopicAnalytics", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "TopicAnalytics");
        }
    }
}
