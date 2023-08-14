$(document).ready(function() {
	const navTabs = $('.prod-navs').find('.nav-link').toArray();
	const protocol = $('.prod-navs').data('secure') === true ? 'https' : 'http';
	const relativePath = $('.prod-navs').data('domain'); //domain site name
	const indexPagePath = `${protocol}://${relativePath}/`;  //creating main page URL
    const currentPath = location.href;
	const currentPathParts = currentPath.split('/');
	const isIndexPage = currentPath === indexPagePath ? true : false;
    var currentActiveTab;

	//filling array with text, that located on tabs
	//first tab are not consider
    var navsText = []
    for (var i = 1; i < navTabs.length; i++) {
        navsText.push($(navTabs[i]).contents()[2].data.trim().toLowerCase())
    }
	//recognizing tab index, that corresponds by current URL(+1 -> tab "All" not consider)
	var indexesArray = navsText.map(element => currentPathParts.indexOf(element));
    var searchIndex = indexesArray.map(element => (element >= 0 ? indexesArray.indexOf(element) : null)).filter(element => element !== null)[0] + 1;

	//tab "All" is active if either it's the main page or the page of sorting all products or main list pagination is active
	if(isIndexPage || currentPath.includes('mainlist') || currentPath.startsWith('?page', indexPagePath.length)) {
		currentActiveTab = navTabs[0];
	} else {

		for (var i = 1; i < navTabs.length; i++) {
			var href = $(navTabs[i]).attr('href');
			//recognizing active tab (excluding main page)
			if ((currentPath.includes(href) || i === searchIndex ) && href !== '/') {
				currentActiveTab = navTabs[i];
				break
			}
		}
	}
        $(currentActiveTab).addClass('active-nav');
})