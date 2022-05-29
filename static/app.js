var train_data = {
    name: "",
    file: null,
    en_no: ""
};

var recognize_data = {
    file: null,
    subject: ""
};


var message = null;
var active_section = null;


function render(){

   // clear form data

   $('.form-item input').val('');
   $('.tabs li').removeClass('active');
   $('.tabs li:first').addClass('active');


   active_section = 'train-content';

    $('#'+active_section).show();


}
function update(){


    if(message){
        // render message

        $('.message').html('<p class="'+_.get(message, 'type')+'">'+_.get(message, 'message')+'</p>');
    }else{
        $('.message').html('');
    }

    $('#train-content, #recognize-content').hide();
    $('#'+active_section).show();



}


$(document).ready(function(){

    // listen to confirm submit
    $('#confirm-content').submit(function(e){
        var confirm_att = new FormData();
        confirm_att.append('confirm_att', 1);

        axios.get('/api/confirm', confirm_att).then(function(response){

            console.log("Marking attendance of ", response.data.user.id);
            message = {type: 'success', message: 'Attendance marked for: '+ response.data.user.id};
            update();

        }).catch(function(err){

            message = {type: 'error', message: _.get(err, 'response.data.error.message', 'Unknown error')};
            update();

        });

        // call to backend

        e.preventDefault();
    });

    // listen for file added

    $('#train #input-file').on('change', function(event){



        //set file object to train_data
        train_data.file = _.get(event, 'target.files[0]', null);


    });

    // listen for name change
    $('#name-field').on('change', function(event){

        train_data.name = _.get(event, 'target.value', '');

    });


    // listen for en no change
    $('#en_no').on('change', function(e){

        train_data.en_no = _.get(e, 'target.value', '');

    });

    // listen for subject change
    $('#subject').on('change', function(event){

        recognize_data.subject = _.get(event, 'target.value', '');

    });

    // listen tab item click on

    $('.tabs li').on('click', function(e){

        var $this = $(this);


        active_section = $this.data('section');

        // remove all active class

        $('.tabs li').removeClass('active');

        $this.addClass('active');

        message = null;

        update();



    });


    // listen the form train submit

    $('#train').submit(function(event){

        message = null;

        if(train_data.name && train_data.file && train_data.en_no){
            // do send data to backend api

            var train_form_data = new FormData();

            train_form_data.append('name', train_data.name);
            train_form_data.append('file', train_data.file);
            train_form_data.append('en_no', train_data.en_no);

            axios.post('/api/train', train_form_data).then(function(response){

                message = {type: 'success', message: 'Training has been done, user with id is: ' + _.get(response, 'data.id')};

                train_data = {name: '', file: null, en_no: ''};
                update();

            }).catch(function(error){


                  message = {type: 'error', message: _.get(error, 'response.data.error.message', 'Unknown error.')}

                  update();
            });

        }else{

            message = {type: "error", message: "Name and face image is required."}



        }

        update();
        event.preventDefault();
    });


    // listen for recognition form submit

    $('#recognize').submit(function(e){
        e.preventDefault();
        let c = document.getElementById('canvas');
        c.toBlob((blob) => {
        let file = new File([blob], "fileName.jpg", { type: "image/jpeg" })
        var recog_form_data = new FormData();
        console.log(file);
        recog_form_data.append('file', file);
        recog_form_data.append('subject', subject)
        axios.post('/api/recognize', recog_form_data).then(function(response){


            console.log("Marking attendance of ", response.data.user.id);

            message = {type: 'success', message: 'Confirm to mark attendance of '+ response.data.user.id};

            recognize_data = {file: null, subject: ''};
            update();

        }).catch(function(err){


            message = {type: 'error', message: _.get(err, 'response.data.error.message', 'Unknown error')};

            update();

        });
        }, 'image/jpeg');

        // call to backend

        e.preventDefault();
    });


const player = document.getElementById('player');
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');
const captureButton = document.getElementById('capture');

const constraints = {
video: true,
};

captureButton.addEventListener('click', () => {
// Draw the video frame to the canvas.
context.drawImage(player, 0, 0, canvas.width, canvas.height);
});

// Attach the video stream to the video element and autoplay.
navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
player.srcObject = stream;
});

// render the app;
render();

});