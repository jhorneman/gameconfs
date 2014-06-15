module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    cssmin: {
      combine: {
        files: {
          'gameconfs/static/css/all.min.css': [
              'gameconfs/static/css/jquery-ui.css',
              'gameconfs/static/css/bootstrap.min.css',
              'gameconfs/static/css/gameconfs.css'
          ]
        }
      }
    },

    uglify: {
      combine: {
        files: {
          'gameconfs/static/js/all.min.js': [
              'gameconfs/static/js/jquery-1.9.1.js',
              'gameconfs/static/js/jquery-ui.js',
              'gameconfs/static/js/bootstrap.js',
              'gameconfs/static/js/main.js'
          ]
        }
      }
    },

    watch: {
      css: {
        files: ['gameconfs/static/css/gameconfs.css'],
        tasks: ['cssmin'],
        options: {
          livereload: true
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask('default', ['cssmin', 'uglify']);
  grunt.registerTask('dev', ['watch']);
};