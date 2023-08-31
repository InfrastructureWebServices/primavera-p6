var server_send_listener;
document.addEventListener('DOMContentLoaded', function () {
    var status_title = $('#status');
    var progress_bar = $("#progress-bar").find('div');
    var progress_message = $('#progress-message');
    var cancel_button = $('#cancel');
    var restart_button = $('#restart');
    var download_button = $('#download');
    var listener = setInterval(function () {
        let request = new XMLHttpRequest();
        request.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                let { stage, i, n } = JSON.parse(this.responseText);
                switch (stage) {
                    case "queued":
                        {
                            status_title.text('Queued... waiting for other packages to complete');
                        }
                        break;
                    case "processing worklots":
                        {
                            i = parseInt(i);
                            n = parseInt(n);
                            if (i < n) {
                                status_title.text('Downloading work lot files');
                                let message = `Work lot ${i} of ${n} - ${(i / n * 100).toFixed(0)}%`;
                                progress_message.text(message);
                                let percent_complete = `${(i / n * 100).toFixed(0)}%`;
                                progress_bar.css('width', percent_complete);
                                progress_bar.attr('class', "determinate");
                            }
                        }
                        break;
                    case "creating zip":
                        {
                            status_title.text('Zipping files together');
                            progress_bar.removeAttr('style');
                            progress_bar.attr('class', "indeterminate");
                            progress_message.hide();
                        }
                        break;
                    case "ready for download":
                        {
                            status_title.text('Ready');
                            $("#progress-bar").hide();
                            cancel_button.hide();
                            restart_button.hide();
                            download_button.show();
                            clearInterval(listener);
                        }
                        break;
                    case "error":
                        {
                            status_title.text('Error');
                            status_title.css('color', 'red')
                            progress_bar.css('color', 'red');
                            cancel_button.hide();
                            restart_button.show();
                            download_button.hide();
                            clearInterval(listener);
                        }
                        break;
                }
            }
        }
        request.open("GET", `../../status?package=${uuid}`, true);
        request.send();
    }, 1000);
});
