using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace OBDInsightBot.Migrations
{
    /// <inheritdoc />
    public partial class addingTopicsToUseCaseMateics : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ListOfTopics",
                table: "SignleUses",
                type: "TEXT",
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<bool>(
                name: "ManualDataEntry",
                table: "SignleUses",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ListOfTopics",
                table: "SignleUses");

            migrationBuilder.DropColumn(
                name: "ManualDataEntry",
                table: "SignleUses");
        }
    }
}
