var gulp = require('gulp');
var concat = require('gulp-concat');
var less = require('gulp-less');
var browserify = require('browserify');
var source = require('vinyl-source-stream');
var buffer = require('vinyl-buffer');
var gutil = require('gulp-util');
var process = require('child_process');

gulp.task('fonts', function(){
  return gulp.src('./node_modules/bootstrap/fonts/*.{ttf,woff,woff2,eot,svg}')
    .pipe(gulp.dest('./frontend/build/fonts/'))
});

gulp.task('img', function(){
  return gulp.src('./frontend/img/*.{png,jpg}')
    .pipe(gulp.dest('./frontend/build/img/'))
});

gulp.task('voicemail', function(){
  return gulp.src('./frontend/voicemail/*')
    .pipe(gulp.dest('./frontend/build/voicemail/'))
});

gulp.task('admin_js', function(){
  return browserify({
    entries: './frontend/js/admin_entry.js',
    debug: true,
    // defining transforms here will avoid crashing your stream
    transform: []
  }).bundle()
    .pipe(source('admin.js'))
    .pipe(buffer())
    .on('error', function(e) {
        gutil.log(e.stack);
        this.emit('end');
    })
    .pipe(gulp.dest('./frontend/build/js/'));
});


gulp.task('stats_js', function(){
  return browserify({
    entries: './frontend/js/stats_entry.js',
    debug: true,
    // defining transforms here will avoid crashing your stream
    transform: []
  }).bundle()
    .pipe(source('stats.js'))
    .pipe(buffer())
    .on('error', function(e) {
        gutil.log(e.stack);
        this.emit('end');
    })
    .pipe(gulp.dest('./frontend/build/js/'));
});



gulp.task('watch', function(){
  gulp.watch('./frontend/js/**/*.js', ['admin_js', 'stats_js']);
})

gulp.task('django', function(){
  var spawn = process.spawn;
  console.info('Starting django server');
  spawn('python', ['manage.py','runserver'], {stdio: 'inherit'});
});


gulp.task('build', [
  'fonts', 'img', 'voicemail', 'less_dev', 'admin_js', 'stats_js'])
gulp.task('default', ['django', 'build', 'watch'])
