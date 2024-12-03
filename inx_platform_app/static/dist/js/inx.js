function handleRefreshButtonClick() {
  console.log('Handling refresh button click');
  // Find the "refresh BDG" button by its ID
  var refreshButton = document.getElementById('refresh-budget-button');
  console.log(refreshButton);
  if (refreshButton) {
    refreshButton.click();
  }
}

  document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded inside inx.js')
    // Call handleForecastAreaUpdate function after page load
    handleRefreshButtonClick();
  });

  document.addEventListener('htmx:afterSwap', function(event) {
    console.log('afterSwap happened');
    // Check if the request was a POST request to forecast-save or budget-save
    if (event.detail.target.id === 'forecast-area') {
      handleRefreshButtonClick();
      }
    }
  );