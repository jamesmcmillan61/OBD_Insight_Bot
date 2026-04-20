using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace OBDInsightBot.Migrations
{
    /// <inheritdoc />
    public partial class InitalisingAnalytics2 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "UploadFileSucsessfully",
                table: "SignleUses",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "UploadFileSucsessfully",
                table: "SignleUses");
        }
    }
}
