





$( document ).ready(function() {


        

    // Activity cards are sortable
    $( ".sortable" ).sortable({
        tolerance: "pointer",
        connectWith: ".sortable",
        revert: true,
        
        // Maintain approximate same width while being dragged
        start: function(event, ui){
            $(ui.item).css("width", "93%");
        }   
    });
    
    // Activity cards are sortable
    $( ".sortable-list" ).sortable({
        tolerance: "pointer",
        revert: true,
        

    });
    
    $( "#col-1-sortable" ).droppable({
        drop: function( event, ui ) {
            card_id = $(ui.draggable).attr("data-id");
            $(ui.draggable).attr("data-column", "1");
            
            window.location.href = "/edit-card-column/" + card_id + "/" + 1;
        }
    });
    $( "#col-2-sortable" ).droppable({
        drop: function( event, ui ) {
           card_id = $(ui.draggable).attr("data-id");
            $(ui.draggable).attr("data-column", "2");
            
            window.location.href = "/edit-card-column/" + card_id + "/" + 2;
        }
    });
    $( "#col-3-sortable" ).droppable({
        drop: function( event, ui ) {
            card_id = $(ui.draggable).attr("data-id");
            $(ui.draggable).attr("data-column", "3");
            
            window.location.href = "/edit-card-column/" + card_id + "/" + 3;
        }
    });
    $( "#col-4-sortable" ).droppable({
        drop: function( event, ui ) {
            card_id = $(ui.draggable).attr("data-id");
            $(ui.draggable).attr("data-column", "4");
            
            window.location.href = "/edit-card-column/" + card_id + "/" + 4;
        }
    });
    
    $('.datepicker').datepicker();
    
    // A custom spinner is used as bootstrap prevents jqueryui spinner
    // from working,
    $(document).on('click', '.number-spinner button', function () {    
	    var btn = $(this),
    		oldValue = btn.closest('.number-spinner').find('input').val().trim(),
    		newVal = 0;
	
	    if (btn.attr('data-dir') == 'up') {
		    newVal = parseFloat(oldValue) + .25;
    	} else {
    		if (oldValue > 0.25) {
    			newVal = parseFloat(oldValue) - .25;
    		} else {
    			newVal = .25;
    		}
    	}
    	btn.closest('.number-spinner').find('input').val(newVal);
    });
    
    $(document).ready(function() {
        $("#reset").click(function() {
            $("input").val("");
            $("textarea").val("");
            $("textarea").val("");
            $("#hours").val("1");
        });
    });

        
    // Determine window size
    window.onload=function(){
        var borderWidth = getBorderWidth();
        adjustBorder(borderWidth);
    };
    
    // On large screens the column titles are in a separate 
    // bootstrap row from the kanban board. These column titles
    // would all display together at the top when the screen
    // size is reduced. Thus, on small screens, different title
    // elements are used that are within the kanban board row.
    window.onresize = function changeTitles() {
            
    if ($(window).width() < 992) {
        //small screen, load other JS files
        $( ".big-title" ).hide();
        $( ".small-title" ).show();  
        $( ".panel-group" ).css("width", "100%");  
    } else {
        $( ".big-title" ).show();
        $( ".small-title" ).hide();  
        $( ".panel-group" ).css("width", "100%");  
    }

 
};

if ($(window).width() < 992) {
    //small screen, load other JS files
    $( ".big-title" ).hide();
    $( ".small-title" ).show();  
    $( ".panel-group" ).css("width", "100%");  
} else {
    $( ".big-title" ).show();
    $( ".small-title" ).hide();  
    $( ".panel-group" ).css("width", "100%");  
}


});

function addCard() {
   document.getElementById("add-card-form").submit();
}

function editCard(card_id) {
    document.getElementById("edit-card-form-" + card_id).submit();
}

function addBoard(board_id) {
   document.getElementById("add-board-form").submit();
}

function editBoard(board_id) {
   document.getElementById("edit-board-form-" + board_id).submit();
}

function editCardCollapse(card_id) {
    var collapsed;
    
    // The class 'in' actually indicates that it's not collapsed
    // but this method runs before that class has been added.
    if ($( "#collapse-" + card_id ).hasClass( "in" )) {
        collapsed = true;
    } else {
        collapsed = false;
    }
    
    window.location.href = "/edit-card-collapse/" + card_id + "/" + collapsed;
}

$(function () // on document.ready()
{
    if ($('#boards-list').length > 0) {
        
    }
});