var gulp = require('gulp');
var concat = require('gulp-concat');
var less = require('gulp-less');
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

gulp.task('less_dev', function(){
  return gulp.src('./frontend/less/main.less')
    .pipe(less())
    .pipe(gulp.dest('./frontend/build/css/'));
});

gulp.task('watch', function(){
  gulp.watch('./frontend/less/**/*.less', ['less_dev']);
})

gulp.task('django', function(){
  var spawn = process.spawn;
  console.info('Starting django server');
  var PIPE = {stdio: 'inherit'};
  spawn('python', ['manage.py','runserver'], PIPE);
});


gulp.task('build', ['fonts', 'img', 'voicemail', 'less_dev'])
gulp.task('default', ['django', 'build', 'watch'])