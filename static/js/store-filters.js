// HOODRANKED store page: filter + sort panel behavior.
document.addEventListener("DOMContentLoaded", () => {
  const filterToggle = document.getElementById("filter-toggle");
  const filterPanel = document.getElementById("filter-panel");
  const closeFilter = document.getElementById("close-filter");

  filterToggle?.addEventListener("click", () => {
    filterPanel.classList.toggle("hidden");
    filterPanel.style.maxHeight = filterPanel.classList.contains("hidden")
      ? "0"
      : filterPanel.scrollHeight + "px";
  });
  closeFilter?.addEventListener("click", () => {
    filterPanel.style.maxHeight = "0";
    setTimeout(() => filterPanel.classList.add("hidden"), 500);
  });

  const sortToggle = document.getElementById("sort-toggle");
  const sortPanel = document.getElementById("sort-panel");
  const closeSort = document.getElementById("close-sort");

  sortToggle?.addEventListener("click", () => {
    sortPanel.classList.toggle("hidden");
    sortPanel.style.maxHeight = sortPanel.classList.contains("hidden")
      ? "0"
      : sortPanel.scrollHeight + "px";
  });
  closeSort?.addEventListener("click", () => {
    sortPanel.style.maxHeight = "0";
    setTimeout(() => sortPanel.classList.add("hidden"), 500);
  });

  document.getElementById("apply-filters")?.addEventListener("click", () => {
    const collection = document.getElementById("collection").value;
    const minPrice = document.getElementById("min_price").value;
    const maxPrice = document.getElementById("max_price").value;
    const url = new URL(window.location.href);
    url.searchParams.delete("page");
    collection ? url.searchParams.set("collection", collection) : url.searchParams.delete("collection");
    minPrice ? url.searchParams.set("min_price", minPrice) : url.searchParams.delete("min_price");
    maxPrice ? url.searchParams.set("max_price", maxPrice) : url.searchParams.delete("max_price");
    window.location.href = url.toString();
  });

  document.getElementById("apply-sort")?.addEventListener("click", () => {
    const sort = document.getElementById("sort").value;
    const url = new URL(window.location.href);
    url.searchParams.delete("page");
    sort && sort !== "newest" ? url.searchParams.set("sort", sort) : url.searchParams.delete("sort");
    window.location.href = url.toString();
  });
});