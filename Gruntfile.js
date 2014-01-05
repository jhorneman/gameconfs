module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    clean: {
      build: ['build']
    },

    cssmin: {
      combine: {
        files: {
          'build/combined.css': ['gameconfs/static/css/gameconfs.css', 'gameconfs/static/css/datepicker.css']
        }
      }
    },

    uglify: {
      combine: {
        files: {
          'build/combined.js': ['gameconfs/static/js/*.js']
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');

  grunt.registerTask('default', ['clean', 'cssmin', 'uglify']);
};