# Deployment Guide

This document outlines the planned deployment process and infrastructure configuration for the IBM OBD InsightBot application.

**Status**: Closing phase - finishing touches
- Azure resources created
- CI/CD pipelines configured
- configuration files exist
- This document serves as deployment planning for future implementation

## Deployment Overview 

The IBM OBD InsightBot will eventually be deployed as a cloud-hosted web application with:

- **Frontend**: Blazor WebAssembly (static files) 
- **Backend**: ASP.NET Core Web API 
- **Database**: SQL Server 
- **AI Service**: IBM Granite 1B (self-hosted on VM with resource constraints)
- **Hosting Platform**: To be determined (Azure or other options under consideration)

**Current Status**: Application is in documentation/closing phase.

## Environment Strategy

### Development Environment (Current)
**Purpose**: Local development and testing

**What Exists Now**:
- Local machines with .NET 8.0 SDK installed
- Visual Studio/VS Code for development
- Jupyter notebooks for IBM Granite 1B experimentation
- appsettings.Development.json
- SQL Server LocalDB configuration 
- API configuration 


### Staging Environment (Plans)
**Purpose**: Pre-production testing and validation (once implementation begins)

**Planned Infrastructure**:
- Hosting platform TBD
- Database TBD
- Self-hosted Granite 1B model on VM

### Production Environment (Plans)
**Purpose**: Live application for end users (future)

**Planned Infrastructure**:
- Hosting platform TBD
- Database TBD
- Self-hosted Granite 1B model on VM
- Monitoring solution TBD
.

## Infrastructure Setup (Plans)


**Note**: Hosting platform (Azure, AWS, other) is not yet decided. Commands below are examples if Azure is chosen.

### Planned Resource Group (Example)

If Azure is chosen, will create resource group:

```bash
# EXAMPLE ONLY - NOT EXECUTED YET
az group create \
  --name rg-obd-insightbot \
  --location eastus
```

### Planned Hosting Setup (Example)

If Azure is chosen, potential setup commands:

```bash
# EXAMPLES ONLY - NOT EXECUTED YET
# These are reference examples for future implementation

# Example: App Service Plan
az appservice plan create \
  --name plan-obd-insightbot \
  --resource-group rg-obd-insightbot \
  --sku S1 \
  --is-linux

# Example: Backend API hosting
az webapp create \
  --name app-obd-insightbot-api \
  --resource-group rg-obd-insightbot \
  --plan plan-obd-insightbot \
  --runtime "DOTNETCORE:8.0"
```


### Planned Database Setup (Example)

If SQL Server on Azure is chosen:

```bash
# EXAMPLES ONLY - NOT EXECUTED YET

# Example: SQL Server
az sql server create \
  --name sql-obd-insightbot \
  --resource-group rg-obd-insightbot \
  --location eastus \
  --admin-user sqladmin \
  --admin-password [SecurePassword]

# Example: Database
az sql db create \
  --name sqldb-obd-insightbot \
  --resource-group rg-obd-insightbot \
  --server sql-obd-insightbot \
  --service-objective S0 \
  --backup-storage-redundancy Local
```


### Planned Secrets Management (Example)

If Azure Key Vault is chosen:

```bash
# EXAMPLES ONLY - NOT EXECUTED YET

az keyvault create \
  --name kv-obd-insightbot \
  --resource-group rg-obd-insightbot \
  --location eastus

# Add secrets (example structure)
az keyvault secret set \
  --vault-name kv-obd-insightbot \
  --name "ConfigurationSecret" \
  --value "[Value]"
```

**Current Status**: No secrets management configured yet.

## Configuration Management 


### Environment Variables 

Once application is implemented and deployed, will need environment configuration.

**What Will Be Needed** (examples):
- Connection strings
- Self-hosted Granite 1B model endpoint configuration
- Logging configuration
- Application-specific settings

**Current Status**: Env variables configured

### Configuration Files 

**What Doesn't Exist**:
- No `appsettings.json` files (no code project yet)
- No `appsettings.Development.json` (no code project yet)
- No `appsettings.Production.json` (no code project yet)

**Future Considerations**:
- Will need configuration structure once code implementation begins
- Configuration will depend on:
  - Granite 1B self-hosted model endpoint (TBD)
  - Database connection (TBD)
  - Hosting platform (TBD)


## Database Migration Strategy (Planned)

**Current Status**: No database exists. No Entity Framework code. No migrations.

### Planned Initial Setup (Future)

Once database code is implemented, will use Entity Framework migrations:

```bash
# EXAMPLES FOR FUTURE REFERENCE - NOT APPLICABLE YET

# Add migration tool (when needed)
dotnet tool install --global dotnet-ef

# Generate migration (once EF models exist)
dotnet ef migrations add InitialCreate --project API

# Apply migration (once database is configured)
dotnet ef database update --connection "[Connection String]"
```

**Current Status**: Will be relevant once implementation begins.

### Production Migration Process (Planned)

Planned approach for future:
1. Backup database (once database exists)
2. Generate migration (once EF models exist)
3. Test in staging (once staging environment exists)
4. Apply to production (once production environment exists)
5. Verify functionality


### Rollback Strategy (Planned)

Will be determined once database platform is chosen and implemented.

**Current Status**: Not applicable yet.

## CI/CD Pipeline 

### Planned Pipeline Approach 

Once code implementation exists, will need CI/CD pipeline with:

**Planned Stages**:
1. **Build**: Compile .NET solution (once code exists)
2. **Test**: Run tests (once tests exist)
3. **Code Coverage**: Check coverage requirements (once tests exist)
4. **Deploy**: Deploy to hosting platform (once hosting configured)


**Current Status**: Working

### Pipeline Configuration 

Will need to create pipeline configuration file once:
- Code implementation exists
- Tests are written
- Hosting platform is chosen
- Deployment strategy is finalized

**Current Status**: Working

## Deployment Checklist (Future Reference)

**Current Status**: Checklist for future use.

### Planned Pre-Deployment Checklist (Future)

Once implementation exists:
- [ ] All tests passing (once tests exist)
- [ ] Code coverage ≥ 70% (once tests exist)
- [ ] Code review approved
- [ ] Release notes prepared
- [ ] Database migrations tested (once database exists)
- [ ] Configuration verified (once config exists)
- [ ] Monitoring configured (once monitoring exists)

### Planned Deployment Steps (Future)

Once infrastructure exists:
- [ ] Notify team of deployment window
- [ ] Backup database (once database exists)
- [ ] Deploy to staging (once staging exists)
- [ ] Run tests on staging (once staging exists)
- [ ] Deploy to production (once production exists)
- [ ] Apply database migrations (once database exists)
- [ ] Verify deployment success

### Planned Post-Deployment (Future)

Once deployment happens:
- [ ] Run smoke tests
- [ ] Verify functionality
- [ ] Monitor for errors
- [ ] Check response times (RNF-01: 90% < 3 seconds)
- [ ] Verify Granite 1B model connectivity
- [ ] Update documentation
- [ ] Notify stakeholders

**Current Status**: Checklist for future reference.

## Monitoring and Logging (Planned)

**Current Status**: No monitoring or logging configured.

### Planned Monitoring Approach (Future)

Once application is implemented and deployed, will need:

**Monitoring Considerations**:
- Application telemetry
- Request/response tracking
- Error monitoring
- Performance metrics (3 second target per RNF-01)
- Granite 1B model performance monitoring

**What Doesn't Exist**:
- No monitoring solution configured
- No telemetry collection code
- No logging infrastructure
- No health check endpoints

**Current Status**: Will be implemented during deployment phase.

### Planned Logging (Future)

Once code exists, will need logging configuration:

**Planned Logging Areas**:
- Application events
- Error tracking
- Performance metrics
- Model inference times

**Current Status**: No logging code exists yet.

### Planned Health Checks (Future)

Once API and dependencies exist, will need health check endpoints:

**Planned Health Checks**:
- Database connectivity (once database exists)
- Granite 1B model availability (once hosting configured)
- Application status

**Current Status**: No health check endpoints exist. No code implemented yet.

## Rollback Procedures (Planned)

**Current Status**: Procedures for future reference.

### Planned Application Rollback (Future)

Once deployment infrastructure exists, will need rollback procedures.

**What Will Be Needed**:
- Deployment slot strategy (if applicable)
- Version control for deployments
- Rollback automation

**Current Status**: Not applicable - no deployments yet.

### Planned Database Rollback (Future)

Once database exists, will need:
- Backup strategy
- Restore procedures
- Migration rollback approach

**Current Status**: Not applicable - no database exists yet.

## Security Considerations (Planned - NOT IMPLEMENTED)

**Current Status**: No code exists to secure. Security measures for future implementation.

### Planned Security Measures (Future)

Once application is implemented, will need:

**HTTPS Configuration**:
- Enforce HTTPS connections
- Configure SSL/TLS certificates

**Authentication & Authorization**:
- Session management
- Secure API access

**Configuration Security**:
- Secure secret storage
- API key protection
- Never log sensitive information

**Input Validation**:
- File size limits (5MB per FR-05)
- File format validation
- SQL injection prevention (Entity Framework)
- XSS prevention (Blazor)

**Current Status**: No security implementation exists. No CORS configuration. No code to secure yet.

## Performance Optimization (Planned)

**Current Status**: Code exists to optimize. Performance considerations for future.

### Performance Requirements (From Requirements.md)

**Target Requirements** (RNF-01):
- 90% of queries < 3 seconds
- File upload < 5 seconds (for 5MB files)

**Planned Optimization Strategies** (Future):
- Connection pooling (once database exists)
- Efficient model inference (Granite 1B CPU-optimized)
- Caching (future enhancement)
- Response compression (once API exists)

**Current Status**: Will be addressed during implementation and testing phase.

## Backup and Disaster Recovery (Planned)

**Current Status**: No database or application to back up yet.

### Planned Backup Strategy (Future)

Once database is implemented, will need:
- Automated backup schedule
- Backup retention policy
- Backup testing procedures

**Current Status**: Not applicable - no database exists yet.

### Planned Disaster Recovery (Future)

Once application is deployed, will need:
1. Monitoring for issues
2. Incident response procedures
3. Backup restoration procedures
4. Testing and verification
5. Post-incident documentation

**Current Status**: Not applicable - no deployment exists yet.

## Cost Estimation (Preliminary)

**Current Status**: TBD

### Estimated Infrastructure Costs (Once Deployed)

Hosting costs will depend on chosen platform. Example if Azure is selected:

| Resource | Estimated Cost |
|----------|----------------|
| Hosting (TBD) | TBD |
| Database (TBD) | TBD |
| VM for Granite 1B | Included (existing VM) |
| Monitoring (TBD) | TBD |



## Summary

**Current Reality**:
- This document describes **planned deployment approaches only**


**What Exists Now**:
- Development environment with .NET 8.0 SDK and development tools
- Jupyter notebooks for IBM Granite 1B experimentation
- VM available for future Granite 1B hosting (low RAM, CPU only)
- Documentation and planning (this document)
- backend code
- frontend code
- API endpoints
- database implementation
- deployment infrastructure
- CI/CD automation
- monitoring or logging

**What Doesn't Exist**:

- No security implementation

- 
**Next Steps** (Once Implementation Begins):
- Configure security measures


## Related Documentation

- [Getting Started](./Getting-Started.md) - Local development setup
- [System Architecture](./System-Architecture.md) - Application architecture
- [Troubleshooting](./Troubleshooting.md) - Common deployment issues
- [Hosting](./SETUP-SINGLE-WINDOWS-VM.md) - How to host the app

---

**Last Updated**: March 2026
**Maintained By**: IBM OBD InsightBot Team
