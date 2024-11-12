function fetchPosts() {
    fetch('/api/posts')
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch posts");
            }
            return response.json();
        })
        .then(feed => {
            const feedContainer = document.getElementById("feed");
            feedContainer.innerHTML = '';

            feed.forEach(post => {
                // Create Bootstrap Card
                const postDiv = document.createElement("div");
                postDiv.classList.add("card", "shadow-sm", "mb-3");

                // Profile Header with Image
                const postHeader = document.createElement("div");
                postHeader.classList.add("card-header", "d-flex", "align-items-center");

                postHeader.innerHTML = `
                    <a href="/profile?id=${post.user_id}">
                        <img src="static/uploads/${post.profile_photo}" alt="Profile Picture" class="rounded-circle me-3" style="width: 40px; height: 40px; object-fit: cover;">
                    </a>
                    <div class="flex-grow-1">
                        <h5 class="mb-0">${post.username}</h5>
                        <small class="text-muted">${ new Date(post.timestamp).toLocaleString(
                            'en-US', {
                                        year: 'numeric',
                                        month: 'short',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                }
                            )}
                        </small>
                    </div>
                `;
                postDiv.appendChild(postHeader);

                // Post Content
                const postContent = document.createElement("div");
                postContent.classList.add("card-body");
                postContent.innerHTML = `<p class="card-text">${post.content}</p>`;
                postDiv.appendChild(postContent);

                // Post Stats
                const postStats = document.createElement("div");
                postStats.classList.add("card-footer", "text-muted");

                postStats.innerHTML = `
                    <span class="me-2">${post.like_count} Likes</span>
                    <a href="/comment?post_id=${post.id}" class="text-secondary text-decoration-none">
                        <span>${post.comment_count} Comments</span>
                    </a>
                `;
                postDiv.appendChild(postStats);

                // Post Actions (Buttons)
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
        })
        .catch(error => {
            console.error("Error loading feed:", error);
            document.getElementById("feed").innerHTML = "<p class='text-danger'>Failed to load posts.</p>";
        });
}



// Call fetchPosts when the page loads
window.onload = fetchPosts;
