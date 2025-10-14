using Microsoft.EntityFrameworkCore;

namespace WebApplication_Icrisat.Models
{
    public class IcristatDbContext : DbContext
    {
        public IcristatDbContext(DbContextOptions<IcristatDbContext> options)
            : base(options)
        {
        }

        public DbSet<Characterization> Characterizations { get; set; }
        public DbSet<PassportData> PassportData { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Characterization>().ToTable("charecterstics");
            modelBuilder.Entity<PassportData>().ToTable("passport_data");

            // Define primary key for Characterization
            modelBuilder.Entity<Characterization>()
                .HasKey(c => c.ICRISATAccessionIdentifier);

            // Define primary key for PassportData
            modelBuilder.Entity<PassportData>()
                .HasKey(p => p.ICRISATAccessionIdentifier);
        }
    }
}