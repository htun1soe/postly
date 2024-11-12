// Get the query string from the URL
const queryString = window.location.search;

// Use URLSearchParams to parse it
const urlParams = new URLSearchParams(queryString);
const user_id = urlParams.get("id"); 

fetch(`/api/profile/${user_id}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            const error = document.querySelector("#error-message");
            error.style.display = "block";
            const h1 = document.createElement("h1");
            h1.innerHTML = data.error;

            error.prepend(h1);
            document.querySelector(".main-content").style.display = "none";
        }
        else {
            document.querySelector(".main-content").style.display = "block";
            displayProfilePhoto(data.profile_photo);

            document.querySelector("#username").textContent = data.username;
            document.querySelector("#bio").textContent = data.bio;
            document.querySelector("#followers").textContent = `${data.followers} followers`;
            const feedContainer = document.getElementById("posts");
            feedContainer.innerHTML = "";

            data.posts.forEach(post => {

                const postDiv = document.createElement("div");
                postDiv.classList.add("card", "shadow-sm", "mb-3");

                const postHeader = document.createElement("div");
                postHeader.classList.add("card-header", "d-flex", "align-items-center");

                postHeader.innerHTML = `
                <a href="/profile?id=${post.user_id}">
                    <img src="static/uploads/${post.profile_photo}" alt="Profile Picture" class="rounded-circle me-3" style="width: 40px; height: 40px; object-fit: cover;">
                </a>
                <div class="flex-grow-1">
                    <h5 class="mb-0">${post.username}</h5>
                    <small class="text-muted">${new Date(post.timestamp).toLocaleString()}</small>
                </div>
            `;
                postDiv.appendChild(postHeader);

                const postContent = document.createElement("div");
                postContent.classList.add("card-body");
                postContent.innerHTML = `<p class="card-text">${post.content}</p>`;
                postDiv.appendChild(postContent);

                const postStats = document.createElement("div");
                postStats.classList.add("card-footer", "text-muted");

                postStats.innerHTML = `
                            <span class="me-2">${post.like_count} Likes</span>
                            <a class="text-secondary text-decoration-none" href="/comment?post_id=${post.id}">
                                <span>${post.comment_count} Comments</span>
                            </a>
                        `;
                postDiv.appendChild(postStats);

                const postActions = document.createElement("div");
                postActions.classList.add("card-footer", "d-flex", "gap-2");
                postActions.innerHTML = `
                    <form action="/like" method="post">
                        <input name="post_id" type="hidden" value="${post.id}">
                        <button class="btn btn-primary btn-sm" type="submit">Like</button>
                    </form>
                    <a href="/comment?post_id=${post.id}">
                        <button class="btn btn-secondary btn-sm">Comment</button>
                    </a>
                        `;
                postDiv.appendChild(postActions);

                feedContainer.appendChild(postDiv);
            });
        }
    })
    .catch(error => {
        console.log('Error:', error);
    })

function displayProfilePhoto(url) {
    const img = document.querySelector("#profile-photo");

    if (url) {
        img.src = `static/uploads/${url}`;
    } else {
        img.src = "static/uploads/default.png";
    }

}
