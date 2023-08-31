var server_send_listener;
document.addEventListener('DOMContentLoaded', function () {
    var status_title = $('#status');
    var progress_bar = $("#progress-bar").find('div');
    var progress_message = $('#progress-message');
    var listener = setInterval(function () {
        let request = new XMLHttpRequest();
        request.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                let { i, n, stage } = JSON.parse(this.responseText);
                status_title.text(stage);
                switch (stage) {
                    case "Getting worklot documents":
                    case "Getting linked documents":
                        {
                            i = parseInt(i);
                            n = parseInt(n);
                            if (i < n) {
                                status_title.text(stage);
                                let message = `Document ${i} of ${n} - ${(i / n * 100).toFixed(0)}%`;
                                progress_message.text(message);
                                let percent_complete = `${(i / n * 100).toFixed(0)}%`;
                                progress_bar.css('width', percent_complete);
                                progress_bar.attr('class', "determinate");
                            }
                        }
                        break;
                    case "Extracting zip":
                    case "Compiling":
                        {
                            status_title.text(stage);
                            progress_bar.removeAttr('style');
                            progress_bar.attr('class', "indeterminate");
                            progress_message.hide();
                        }
                        break;
                    case "Done":
                        {
                            status_title.text(stage);
                            $("#progress-bar").hide();
                            clearInterval(listener);
                        }
                        break;
                }
            }
        }
        request.open("GET", `./status?sync`, true);
        request.send();
    }, 1000);
});
