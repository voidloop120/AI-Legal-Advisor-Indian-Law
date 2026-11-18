// AI Legal Advisor - Frontend interactions
// Backend/API integration will be added later.

const searchInput = document.getElementById("searchInput");

searchInput.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    const query = searchInput.value.trim();

    if (!query) {
      alert("Please enter a legal search or question.");
      return;
    }

    alert(`Search feature coming soon.\n\nYour query: ${query}`);
  }
});

// Sidebar active state
document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", function (event) {
    event.preventDefault();

    document.querySelectorAll(".nav-item").forEach(nav => {
      nav.classList.remove("active");
    });

    this.classList.add("active");
  });
});

// Feature cards
document.querySelectorAll(".feature-card, .tool-card").forEach(card => {
  card.addEventListener("click", function () {
    const title = this.querySelector("h3")?.textContent || "Feature";
    alert(`${title}\n\nThis page will be connected to the backend later.`);
  });
});
