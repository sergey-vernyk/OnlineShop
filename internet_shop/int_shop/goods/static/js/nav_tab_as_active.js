$(document).ready(function() {
	const navTabs = $('.prod-navs').find('.nav-link').toArray();
	const protocol = $('.prod-navs').data('secure') === true ? 'https' : 'http';
	const relativePath = $('.prod-navs').data('domain'); //имя домена сайта
	const indexPagePath = `${protocol}://${relativePath}/`;  //создание адреса главной страницы
    const currentPath = location.href;
	const currentPathParts = currentPath.split('/');
	const isIndexPage = currentPath === indexPagePath ? true : false;
    var currentActiveTab;

	//наполнение массива текстом, который находится на вкладках (tabs)
	//первая вкладка All не учитывается
    var navsText = []
    for (var i = 1; i < navTabs.length; i++) {
        navsText.push($(navTabs[i]).contents()[2].data.trim().toLowerCase())
    }
	//определения индекса вкладки, которая соответствует текущему адресу (+1 -> вкладка All не учитываться)
	var indexesArray = navsText.map(element => currentPathParts.indexOf(element));
    var searchIndex = indexesArray.map(element => (element >= 0 ? indexesArray.indexOf(element) : null)).filter(element => element !== null)[0] + 1;

	//активна вкладка All, если это главная страница или страница сортировки всех товаров или активна пагинация главного списка
	if(isIndexPage || currentPath.includes('mainlist') || currentPath.startsWith('?page', indexPagePath.length)) {
		currentActiveTab = navTabs[0];
	} else {

		for (var i = 1; i < navTabs.length; i++) {
			var href = $(navTabs[i]).attr('href');
			//определение активной вкладки (исключается главная страница)
			if ((currentPath.includes(href) || i === searchIndex ) && href !== '/') {
				currentActiveTab = navTabs[i];
				break
			}
		}
	}
        $(currentActiveTab).addClass('active-nav');
})