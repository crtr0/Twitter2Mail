function callApi(url, method, params, callback) {
    new Ajax.Request(url, {
       async: 'async',
       method: method,
       parameters: params,
       onComplete: function(transport) {
          //alert(transport.responseText);
          callback(transport.responseText.evalJSON(true));
       }
     });
}

function unsubUser(response) {
  alert(response.message);
}

function unSubscribe() {
  callApi('/unsub',
          'get',
          {username: $F('username'), email: $F('email')},
          unsubUser);
}

function savedUser(response) {
  alert(response.message);
}

function saveUser() {
  callApi('/user',
          'get',
          {username: $F('username'), email: $F('email'), reply_mode: $F('reply_mode'), digest: $$('input:checked[name="digest"]').pluck('value')},
          savedUser);
}

function createLink() {
  $('rss_link').update('<a href="#{link}">#{link}</a>'.interpolate({link: 'http://search.twitter.com/search.atom?q='+($F('reply_mode') == 1? '+to%3A' : '+%40')+$F('username')}));
  $('rss').show();
}

function gotThread(response) {
  $('thread').update(response)
}


function getThread() {
  callApi('/thread_content',
          'get',
          {thread: window.location.search.toQueryParams()['id']},
          gotThread);  
}