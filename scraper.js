const axios = require('axios');
const cheerio = require('cheerio');

(async () => {
  try {

    const url = 'https://parking.fullerton.edu/parkinglotcounts/mobile.aspx';
    const response = await axios.get(url);
    const $ = cheerio.load(response.data);

    const results = [];

    $('table#GridView_All tr').each((_, row) => {
      const location = $(row).find('.LocationName a, .LocationName span').first().text().trim();
      const totalSpots = $(row).find('span[id^=GridView_All_Label_Avail_]').attr('aria-label');
      const availableSpots = $(row).find('span[id^=GridView_All_Label_AllSpots_]').text().trim();
      const lastUpdated = $(row).find('span[id^=GridView_All_Label_LastUpdated_]').attr('aria-label');

      if (location) {
        results.push({
          structure: location,
          totalSpots,
          availableSpots,
          lastUpdated,
        });
      }
    });

    console.log(results);
  } catch (error) {
    console.error(`Error fetching page: ${error.message}`);
  }
})();