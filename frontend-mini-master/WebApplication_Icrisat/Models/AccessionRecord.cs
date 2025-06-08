namespace WebApplication_Icrisat.Models  // Match the folder/project name
{
    public class AccessionRecord
    {
        public int AccessionIdentifier { get; set; }
        public string Genus { get; set; } = string.Empty;
        public string Species { get; set; } = string.Empty;
        public string DonorCountry { get; set; } = string.Empty;
    }
}
