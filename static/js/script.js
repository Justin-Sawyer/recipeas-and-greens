/* From Materialize (Mobile collapse Button) https://materializecss.com/navbar.html 
and from Code Institute Backend Development Mini Project */
$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
    $('.parallax').parallax();
    $('.tabs').tabs();
    $('.collapsible').collapsible();
    $('.tooltipped').tooltip();
    $('select').formSelect();
    $('.modal').modal();
    $('.fixed-action-btn').floatingActionButton();
    $('#display-cats').click(function(){
        $('#cats').toggle(500);
    });
    $('#display-levs').click(function(){
        $('#levs').toggle(500);
    });

/* Add files to cloudinary and display them online
From Learn with Coffee https://www.youtube.com/watch?v=6uHfIv4981U */
const CLOUDINRY_URL = "https://api.cloudinary.com/v1_1/recipeas-and-greens/upload";
const CLOUDINARY_UPLOAD_PRESET = "b4an3d8o";

var imgPreview = document.getElementById("img-preview");
var fileUpload = document.getElementById("file-upload");
var fileUpload1 = document.getElementById("file-upload1");

fileUpload.addEventListener("change", function(event) {
    var file = event.target.files[0];
    var formData = new FormData();
    formData.append("file", file);
    formData.append("upload_preset", CLOUDINARY_UPLOAD_PRESET);

    axios({
        url: CLOUDINRY_URL,
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data: formData
    }).then(function(res) {
        console.log(res.data.secure_url);
        imgPreview.src = res.data.secure_url;
        /*document.getElementById("img-preview")*/
        /*fileUpload.value = res.data.secure_url;*/
        fileUpload1.value = res.data.secure_url;
    }).catch(function(err) {
        console.log(err);
    });
});

/* From Code Institute Materialize Form Validation video */
validateMaterializeSelect();
    function validateMaterializeSelect() {
        let classValid = { "border-bottom": "1px solid #4caf50", "box-shadow": "0 1px 0 0 #4caf50" };
        let classInvalid = { "border-bottom": "1px solid #f44336", "box-shadow": "0 1px 0 0 #f44336" };
        if ($("select.validate").prop("required")) {
            $("select.validate").css({ "display": "block", "height": "0", "padding": "0", "width": "0", "position": "absolute" });
        }
        $(".select-wrapper input.select-dropdown").on("focusin", function () {
            $(this).parent(".select-wrapper").on("change", function () {
                if ($(this).children("ul").children("li.selected:not(.disabled)").on("click", function () { })) {
                    $(this).children("input").css(classValid);
                }
            });
        }).on("click", function () {
            if ($(this).parent(".select-wrapper").children("ul").children("li.selected:not(.disabled)").css("background-color") === "rgba(0, 0, 0, 0.03)") {
                $(this).parent(".select-wrapper").children("input").css(classValid);
            } else {
                $(".select-wrapper input.select-dropdown").on("focusout", function () {
                    if ($(this).parent(".select-wrapper").children("select").prop("required")) {
                        if ($(this).css("border-bottom") != "1px solid rgb(76, 175, 80)") {
                            $(this).parent(".select-wrapper").children("input").css(classInvalid);
                        }
                    }
                });
            }
        });
    }
});

