document.addEventListener('DOMContentLoaded', function () {

  //fill in average rating of book using 5 stars
  let book_rating = parseFloat(document.querySelector("#average_rating").innerHTML);

  let average_rating = raterJs( {
    element:document.querySelector("#book-rating"),
  })

  average_rating.setRating(book_rating);
  average_rating.disable();


  // fill star rating for the user
  let rating_div = document.querySelector("#user_rating");
  let rating = parseFloat(document.querySelector("#user_rating_data").innerHTML);
  let user_rating = raterJs( {
    element:rating_div,
    rateCallback:function rateCallback(rating, done) {
     this.setRating(rating);
     done();
   }
 });
  user_rating.setRating(rating);

  if (rating_div.classList[0] == "disable_rating")
      user_rating.disable();


  try{
    //handle the submission of a review by a user
    document.querySelector("#submitReview").onclick = function(e)
    {

      //open a post request to send to the server
      let request = new XMLHttpRequest();
      request.open("POST", "/submitReview");

      //display the  new review from the user when the request has successfully reloaded
      request.onload = function()
      {
        let response = JSON.parse(request.responseText);
        console.log(response);
        document.querySelector("#before_review").style.display = "none";
        document.querySelector("#after_review").style.display = "block";
        document.querySelector("#review_content").innerHTML = response.review;

        let user_rating = raterJs( {
          element:document.querySelector("#after_user_rating"),
          rateCallback:function rateCallback(rating, done) {
           this.setRating(rating);
           done();
         }
       });

        let rating = parseFloat(response.rating);
        user_rating.setRating(rating);
        user_rating.disable();
      };


      //send the review and rating submitted by the user to the server
      let review = document.querySelector("#review").value;
      let data = new FormData();
      data.append("review",review);
      data.append("rating", user_rating.getRating());
      request.send(data);
    };

  }
  catch(err){}



  let  otherRating_span = document.querySelectorAll(".other_rating");
  let len = otherRating_span.length;

  let other_ratings = document.querySelector("#others_rating").innerHTML
  other_ratings = other_ratings.split(",");
  other_ratings = other_ratings.slice(1,len+1);


for(var i =0; i < len; i++){
  let rating = parseFloat(other_ratings[i]);
  console.log(rating);
    //fill in average rating of book using 5 stars
    let average_rating = raterJs( {
      element:otherRating_span[i],
    });

    average_rating.setRating(rating);
    average_rating.disable();
  }

  document.querySelector("#edit_button").onclick = function()
  {
    document.querySelector(".review").style.display = "none";
    console.log(document.querySelector("#edit_review"));
    document.querySelector("#edit_review").style.display = "";

    let edit_rating = document.querySelector("#user_rating_edit");

    let user_rating = raterJs( {
      element:edit_rating,
      rateCallback:function rateCallback(rating, done) {
       this.setRating(rating);
       done();
     }
   });

   
 };





});
