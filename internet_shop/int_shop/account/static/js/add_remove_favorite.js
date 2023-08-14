import getCookie from '/static/js/getCSRFToken.js';

var addIcon = `<svg xmlns="http://www.w3.org/2000/svg"
                   width="25" height="25" fill="currentColor" class="bi bi-heart-fill" viewBox="0 0 16 16">
                   <path fill-rule="evenodd" d="M8 1.314C12.438-3.248 23.534 4.735 8 15-7.534 4.736 3.562-3.248 8 1.314z"/>
               </svg>`

var removeIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor"
                        class="bi bi-heart" viewBox="0 0 16 16">
                        <path d="m8 2.748-.717-.737C5.6.281 2.514.878 1.4 3.053c-.523
                        1.023-.641 2.5.314 4.385.92 1.815 2.834 3.989 6.286 6.357
                        3.452-2.368 5.365-4.542 6.286-6.357.955-1.886.838-3.362.314-4.385C13.486.878
                        10.4.28 8.717 2.01L8 2.748zM8 15C-7.333 4.868 3.279-3.04 7.824
                        1.143c.06.055.119.112.176.171a3.12 3.12 0 0 1 .176-.17C12.72-3.042 23.333 4.867 8 15z"/>
                  </svg>`

$(document).ready(function() {
    //on detail view and on watched products list
	$('[id^=remove-fav], #add-rem-fav').click(function() {
		var product_id;
		var action;
		//recognize a button, which was pressed (delete or add)
		if ($(this).attr('id').startsWith('add-')) {
			product_id = $(this).data('pk');
			action = $(this).next('input[name=action]').attr('value'); //necessary action in a hide field
		} else if ($(this).attr('id').startsWith('remove-')) {
			product_id = this.id.slice(11); //getting product id
			action = $(this).data('action');
		}

		var url = $(this).data('url');
		const csrftoken = getCookie('csrftoken');

		$.ajax({
			url: url,
			method: 'POST',
			dataType: 'json',
			data: {
				action: action,
				product_id: product_id,
				csrfmiddlewaretoken: csrftoken,
			},

			success: function(response) {
				var amount_prods = response['amount_prods']; //current products quantity in the favorite
				$('.add-to-favorite > svg').remove();
				if (action === 'remove') {
					$('.add-to-favorite').prepend(removeIcon);
					$(`#fav-prod-${product_id}`).remove(); //deleting block with product in favorite
					//displaying current products quantity in favorite header
					$('.often-use-menu > ul:nth-child(2) > li:nth-child(2) > span:nth-child(1) > a:nth-child(1)').text(amount_prods);
					if (amount_prods === 0) {
						//if there are no products in favorite
						$('.personal-info').append(`<div class="empty-customer-content">
                                                    <h4 class="d-inline">There are no favorite products yet...</h4>
                                                    </div>`);
					}
					$('#add-rem-fav').next('input[name=action]').attr('value', 'add'); //change title on the button
				} else if (action === 'add') {
					$('.add-to-favorite').prepend(addIcon);
					$('#add-rem-fav').next('input[name=action]').attr('value', 'remove');
				}
			},

			error: function(jqXHR, textStatus, errorThrown) {
				//redirection up on login page, if response status is 401
				if(errorThrown === 'Unauthorized') {
					var login_url = jqXHR.responseJSON['login_page_url'];
					window.open(login_url, '_self');
				}
			},
		})
		//function returns necessary action, which is on button text
		function getAction(text) {
			return text.split(' ')[0].toLowerCase();
		}
	});

	//button located on products list on main page
	$('.prod-fav-mainlist').click(function() {
		var childClass = $(this).children().attr('class'); //favorite icon object class
		var action = childClass.includes('fill') ? 'remove' : 'add'; //if icon are filled - product in the favorite
		var url = $(this).data('url');
		var productId = $(this).data('pk');
		const csrftoken = getCookie('csrftoken');

		$.ajax({
			url: url,
			method: 'POST',
			dataType: 'json',
			data: {
				product_id: productId,
				csrfmiddlewaretoken: csrftoken,
				action: action,
			},
			success: function(response) {
				//searching product, that was added/removed into/from favorite
				var currProd = $('.prod-fav-mainlist').filter(function() {
					return Number($(this).attr('data-pk')) === productId;
				});

				//changing icon on opposite
				if (action === 'add') {
					$(currProd).children().replaceWith(addIcon);
				} else if (action === 'remove') {
					$(currProd).children().replaceWith(removeIcon);
				}
			},
			error: function(jqXHR, textStatus, errorThrown) {
				//redirection on login page if response status is 401
				if(errorThrown === 'Unauthorized') {
					var login_url = jqXHR.responseJSON['login_page_url'];
					window.open(login_url, '_self');
				}
			},
		})
	})
})