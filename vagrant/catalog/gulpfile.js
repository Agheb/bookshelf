var gulp = require('gulp');
var browserSync = require('browser-sync');// create a browser sync instance.

var reload = browserSync.reload;
var exec = require('child_process').exec;

//Run Flask server
gulp.task('runserver', function() {
    var proc = exec('python app.py');
});

// Default task: Watch Files For Changes & Reload browser
gulp.task('default', ['runserver'], function () {
  browserSync({
    notify: false,
    browser: "google chrome",
    proxy: "127.0.0.1:5003"

  });
 
  gulp.watch(['templates/*.*'], reload);

});
