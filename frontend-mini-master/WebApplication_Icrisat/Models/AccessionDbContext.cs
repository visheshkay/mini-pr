using Microsoft.EntityFrameworkCore;

namespace WebApplication_Icrisat.Models
{
    public class AccessionDbContext : DbContext
    {
        public AccessionDbContext(DbContextOptions<AccessionDbContext> options)
            : base(options) { }

        public DbSet<AccessionRecord> Accessions { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<AccessionRecord>()
                .ToTable("Passport") 
                .HasKey(a => a.AccessionIdentifier);

            modelBuilder.Entity<AccessionRecord>()
                .Property(a => a.AccessionIdentifier)
                .HasColumnName("ICRISAT accession identifier");

            modelBuilder.Entity<AccessionRecord>()
                .Property(a => a.Genus)
                .HasColumnName("Genus");

            modelBuilder.Entity<AccessionRecord>()
                .Property(a => a.Species)
                .HasColumnName("Species");

            modelBuilder.Entity<AccessionRecord>()
                .Property(a => a.DonorCountry)
                .HasColumnName("Donor Country");
        }
    }
}
