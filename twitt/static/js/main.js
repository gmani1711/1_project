$(document).ready(() => {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip()
  
    // Ajax setup for CSRF token
    function getCookie(name) {
      let cookieValue = null
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";")
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim()
          if (cookie.substring(0, name.length + 1) === name + "=") {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
            break
          }
        }
      }
      return cookieValue
    }
  
    const csrftoken = getCookie("csrftoken")
  
    $.ajaxSetup({
      beforeSend: function (xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
      },
    })
  
    // Like button functionality (global)
    $(document).on("click", ".like-button", function () {
      const postId = $(this).data("post-id")
      const button = $(this)
  
      $.ajax({
        url: `/post/${postId}/like/`,
        type: "POST",
        success: (data) => {
          if (data.liked) {
            button.find("i").removeClass("far").addClass("fas")
            button.addClass("liked")
          } else {
            button.find("i").removeClass("fas").addClass("far")
            button.removeClass("liked")
          }
          button.closest(".card-body").find(".likes-count strong").text(`${data.likes_count} likes`)
        },
      })
    })
  
    // Comment form submission via AJAX
    $(".comment-form").submit(function (e) {
      e.preventDefault()
  
      const form = $(this)
      const url = form.attr("action")
      const formData = form.serialize()
      const input = form.find('input[name="text"]')
  
      $.ajax({
        url: url,
        type: "POST",
        data: formData,
        success: (data) => {
          if (data.success) {
            // Clear the input
            input.val("")
  
            // If on post detail page, add the comment to the list
            if ($(".comments-section").length) {
              const commentHtml = `
                              <div class="comment mb-3">
                                  <div class="d-flex">
                                      <a href="/profile/${data.username}/">
                                          <img src="/media/profile_pics/default.jpg" class="rounded-circle profile-img-xs mr-2" alt="${data.username}">
                                      </a>
                                      <div>
                                          <p class="mb-0">
                                              <a href="/profile/${data.username}/" class="font-weight-bold text-dark">${data.username}</a>
                                              ${data.text}
                                          </p>
                                          <p class="text-muted small mb-0">Just now</p>
                                      </div>
                                  </div>
                              </div>
                          `
              $(".comments-section").append(commentHtml)
            }
          }
        },
      })
    })
  })
  
  