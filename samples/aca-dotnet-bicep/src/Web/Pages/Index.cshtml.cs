using Microsoft.AspNetCore.Mvc.RazorPages;

namespace Web.Pages;

public class IndexModel(AppInfo info) : PageModel
{
    public AppInfo Info => info;

    public void OnGet()
    {
    }
}
