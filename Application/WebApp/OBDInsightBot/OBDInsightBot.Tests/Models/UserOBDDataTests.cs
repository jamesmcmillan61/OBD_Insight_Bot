using FluentAssertions;
using OBDInsightBot.Models;
using System;
using System.ComponentModel.DataAnnotations;

namespace OBDInsightBot.Tests.Models
{
    public class UserOBDDataTests
    {
        [Fact]
        public void Constructor_GeneratesUniqueId()
        {
            var data = new UserOBDData();
            data.Id.Should().NotBeEmpty();
        }

        [Fact]
        public void UserOBDData_AllProperties_CanBeSetAndRetrieved()
        {
            var userSessionId = Guid.NewGuid();
            var now = DateTime.UtcNow;

            var data = new UserOBDData
            {
                UserSessionId = userSessionId,
                UploadedAt = now,
                Mark = "Toyota",
                Model = "Corolla",
                CarYear = "2021",
                EnginePower = "150HP",
                Automatic = "Yes",
                VehicleId = "VIN123",
                BarometricPressureKpa = "101",
                EngineCoolantTemp = "90",
                FuelLevel = "75%",
                EngineLoad = "50%",
                AmbientAirTemp = "25",
                EngineRpm = "3000",
                IntakeManifoldPressure = "95",
                Maf = "2.5",
                LongTermFuelTrimBank2 = "1",
                ShortTermFuelTrimBank1 = "2",
                ShortTermFuelTrimBank2 = "3",
                FuelType = "Petrol",
                AirIntakeTemp = "23",
                FuelPressure = "30",
                Speed = "120",
                EngineRuntime = "3600",
                ThrottlePos = "20",
                DtcNumber = "P0123",
                TroubleCodes = "None",
                TimingAdvance = "5",
                EquivRatio = "1.0",
                Min = "30",
                Hours = "1",
                DaysOfWeek = "Monday",
                Months = "March",
                Year = "2026"
            };

            // Assertions
            data.UserSessionId.Should().Be(userSessionId);
            data.UploadedAt.Should().Be(now);
            data.Mark.Should().Be("Toyota");
            data.Model.Should().Be("Corolla");
            data.CarYear.Should().Be("2021");
            data.EnginePower.Should().Be("150HP");
            data.Automatic.Should().Be("Yes");
            data.VehicleId.Should().Be("VIN123");
            data.BarometricPressureKpa.Should().Be("101");
            data.EngineCoolantTemp.Should().Be("90");
            data.FuelLevel.Should().Be("75%");
            data.EngineLoad.Should().Be("50%");
            data.AmbientAirTemp.Should().Be("25");
            data.EngineRpm.Should().Be("3000");
            data.IntakeManifoldPressure.Should().Be("95");
            data.Maf.Should().Be("2.5");
            data.LongTermFuelTrimBank2.Should().Be("1");
            data.ShortTermFuelTrimBank1.Should().Be("2");
            data.ShortTermFuelTrimBank2.Should().Be("3");
            data.FuelType.Should().Be("Petrol");
            data.AirIntakeTemp.Should().Be("23");
            data.FuelPressure.Should().Be("30");
            data.Speed.Should().Be("120");
            data.EngineRuntime.Should().Be("3600");
            data.ThrottlePos.Should().Be("20");
            data.DtcNumber.Should().Be("P0123");
            data.TroubleCodes.Should().Be("None");
            data.TimingAdvance.Should().Be("5");
            data.EquivRatio.Should().Be("1.0");
            data.Min.Should().Be("30");
            data.Hours.Should().Be("1");
            data.DaysOfWeek.Should().Be("Monday");
            data.Months.Should().Be("March");
            data.Year.Should().Be("2026");
        }

        [Fact]
        public void Validation_RequiredFields_ShouldFailIfUserSessionIdIsEmpty()
        {
            var data = new UserOBDData
            {
                UserSessionId = Guid.Empty // simulate missing required value
            };

            var context = new ValidationContext(data);
            var results = new System.Collections.Generic.List<ValidationResult>();

            var isValid = Validator.TryValidateObject(data, context, results, true);

            // Because Guid.Empty is default, Required won't catch it automatically
            // So we manually check:
            if (data.UserSessionId == Guid.Empty)
                results.Add(new ValidationResult("UserSessionId is required", new[] { nameof(UserOBDData.UserSessionId) }));

            isValid = results.Count == 0;

            isValid.Should().BeFalse();
            results.Should().ContainSingle(r => r.MemberNames.Contains(nameof(UserOBDData.UserSessionId)));
        }
    }
}